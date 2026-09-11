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
            "llm": {
                "provider": "openai",
                "config": {
                    "model": "deepseek-flash",
                    "temperature": 0.0,
                    "api_key": settings.siliconflow_api_key,
                    "openai_base_url": "https://api.siliconflow.cn/v1",
                    "max_tokens": 1500,
                }
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": "Qwen/Qwen3-Embedding-8B", 
                    "api_key": settings.siliconflow_api_key,
                    "openai_base_url": "https://api.siliconflow.cn/v1"
                },
            },
            "vector_store": {"provider": "chroma", "config": {"collection_name": "raphael_memories", "path": "./chroma_db"}},
        }
        self.memory = Memory.from_config(config)

    async def process_input(
        self,
        user_id: str,
        text_content: str = None,
        image_bytes: bytes = None,
        audio_bytes: bytes = None,
    ) -> tuple[str, Any]:
        from core.router import semantic_classify
        from core.omniscience import get_mini_context, log_message
        from core.llm import run_extraction_step, run_response_step, query_causal_graph, _get_llm_client
        from core.hud import build_hud
        from core.search import expand_query, sparse_search, rerank_chunks
        import asyncio
        from datetime import datetime

        if text_content:
            await log_message(int(user_id), "user", text_content)

        mini_ctx = await get_mini_context(int(user_id))
        client = _get_llm_client()
        
        msg_class = await semantic_classify(text_content or "", client)

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
                    messages=[{"role": "user", "content": text}],
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
                CREATE (e:LifeEvent {timestamp: datetime(), description: $desc})
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
                
                await asyncio.to_thread(driver.execute_query, query, params)
            except Exception as e:
                logger.warning("Neo4j log error: %s", e)

        # 4-STEP RAG PIPELINE
        
        # Step 1: Query Expansion & Extraction
        keywords = []
        if text_content:
            keywords = await expand_query(client, text_content)
        
        if msg_class == "data":
            tool_results, impact_flag = await run_extraction_step(int(user_id), text_content or "", mini_ctx)
        
        chunks_tho = []
        
        # Step 2: Hybrid Retrieval
        if impact_flag or msg_class == "deep":
            # 2.1 Graph Search
            graph_results = await query_causal_graph(int(user_id), text_content or "")
            if graph_results:
                chunks_tho.append(f"[GRAPH PATHS]: {graph_results}")
            
            # 2.2 Dense Search (Mem0)
            if text_content:
                mem_results = await asyncio.to_thread(self.memory.search, query=text_content, user_id=user_id, limit=15)
                if mem_results:
                    for m in mem_results:
                        chunks_tho.append(f"[VECTOR MEMORY]: {m.get('memory', '')}")
            
            # 2.3 Sparse Search (SQLite BM25)
            if keywords:
                sparse_res = await sparse_search(keywords, limit=15)
                for s in sparse_res:
                    chunks_tho.append(f"[KEYWORD CHAT LOG]: {s}")
            
            # Step 3: Reranking
            if chunks_tho:
                reranked_chunks = await rerank_chunks(text_content or "", chunks_tho, top_k=15)
                causal_ctx = "
".join(reranked_chunks)

        t1 = asyncio.create_task(_persist_to_graph(tool_results, int(user_id), h3_index, text_content or ""))
        background_tasks.add(t1)
        t1.add_done_callback(background_tasks.discard)
        
        t2 = asyncio.create_task(_add_to_mem0(self.memory, user_id, text_content or ""))
        background_tasks.add(t2)
        t2.add_done_callback(background_tasks.discard)

        # Step 4: Generation
        response = await run_response_step(
            int(user_id), text_content or "", mini_ctx,
            tool_results, impact_flag, causal_ctx
        )

        hud_line, keyboard = await build_hud(int(user_id))
        return f"{response}

{hud_line}", keyboard