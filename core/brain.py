import logging
import asyncio
from typing import Optional, Any
from mem0 import Memory
from config import settings
from datetime import datetime

logger = logging.getLogger(__name__)

# Prevent background tasks from being garbage collected mid-execution
background_tasks = set()

class RaphaelBrain:
    def __init__(self) -> None:
        config = {
            "version": "v1.1",
            "llm": {"provider": "gemini", "config": {"model": "models/gemini-3.5-flash-lite", "api_key": settings.gemini_api_key}},
            "embedder": {
                "provider": "gemini",
                "config": {
                    "model": "gemini-embedding-2-preview",
                    "api_key": settings.gemini_api_key,
                },
            },
            "vector_store": {"provider": "chroma", "config": {"collection_name": "raphael_memories", "path": "./chroma_db"}},
            "graph_store": {"provider": "neo4j", "config": {"url": "neo4j://neo4j:7687", "username": "neo4j", "password": "password"}},
        }
        self.memory = Memory.from_config(config)

    async def process_input(
        self,
        user_id: str,
        text_content: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        audio_bytes: Optional[bytes] = None,
    ) -> tuple[str, Any]:
        from core.router import classify_message
        from core.omniscience import get_mini_context, log_message
        from core.llm import run_extraction_step, run_response_step, query_causal_graph
        from core.hud import build_hud

        if text_content:
            await log_message(int(user_id), "user", text_content)

        mini_ctx = await get_mini_context(int(user_id))
        
        from core.router import semantic_classify
        from core.llm import _get_gemini_client
        msg_class = await semantic_classify(text_content or "", _get_gemini_client())

        
        tool_results, impact_flag, causal_ctx = [], False, ""
        
        try:
            from bot.handlers.location import _location_state
            loc_data = _location_state.get(int(user_id))
            h3_index = loc_data["hex"] if loc_data else None
        except ImportError:
            h3_index = None
        
        async def _add_to_mem0(mem, uid, text):
            try:
                await asyncio.to_thread(
                    mem.add,
                    messages=[
                        {"role": "user", "content": text},
                    ],
                    user_id=uid,
                    metadata={"timestamp": datetime.now().isoformat(), "source": "chat"},
                )
            except Exception as exc:
                logger.warning("Mem0 add failed: %s", exc)

        async def _persist_to_graph(tools, uid, h3_idx, chat_text):
            from core.neo4j_client import get_neo4j_driver
            driver = get_neo4j_driver()
            if not driver:
                return
            try:
                if tools:
                    event_desc = ", ".join([f"{t['tool']}: {t.get('entity', '')}" for t in tools])
                elif chat_text:
                    event_desc = f"Chat: {chat_text}"
                else:
                    return
                
                query = """
                MERGE (u:User {id: $uid})
                CREATE (e:LifeEvent {
                    description: $desc,
                    timestamp: datetime()
                })
                CREATE (u)-[:EXPERIENCED]->(e)
                """
                params = {"uid": uid, "desc": event_desc}
                
                if h3_idx:
                    query += """
                    MERGE (loc:Location {h3: $h3})
                    CREATE (e)-[:HAPPENED_AT]->(loc)
                    """
                    params["h3"] = h3_idx

                if tools:
                    for i, t in enumerate(tools):
                        entity = str(t.get("entity", "")).strip()
                        if entity:
                            param_key = f"ent_{i}"
                            params[param_key] = entity
                            query += f"""
                            MERGE (ent_{i}:Entity {{name: ${param_key}}})
                            CREATE (e)-[:RELATED_TO]->(ent_{i})
                            """
                
                async with driver.session() as session:
                    await session.run(query, **params)
            except Exception as e:
                logger.error("Neo4j _persist_to_graph error: %s", e)

        if msg_class in ("data", "deep"):
            tool_results, impact_flag = await run_extraction_step(
                int(user_id), text_content or "", mini_ctx
            )
            
            if impact_flag:
                entities = [r.get("entity", "") for r in tool_results]
                causal_ctx = await query_causal_graph(int(user_id), entities)

        # Background tasks with strong references
        t1 = asyncio.create_task(_persist_to_graph(tool_results, int(user_id), h3_index, text_content or ""))
        background_tasks.add(t1)
        t1.add_done_callback(background_tasks.discard)
        
        t2 = asyncio.create_task(_add_to_mem0(self.memory, user_id, text_content or ""))
        background_tasks.add(t2)
        t2.add_done_callback(background_tasks.discard)

        response = await run_response_step(
            int(user_id), text_content or "", mini_ctx,
            tool_results, impact_flag, causal_ctx
        )

        # Append HUD
        hud_line, keyboard = await build_hud(int(user_id))
        full_response = response + "\n" + hud_line

        await log_message(int(user_id), "assistant", response)
        
        return full_response, keyboard  # We return tuple as requested

brain = RaphaelBrain()
