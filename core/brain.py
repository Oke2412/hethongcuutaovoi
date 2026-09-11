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
        self.memory: Optional[Memory] = None
        self._init_memory()

    def _init_memory(self) -> None:
        api_key = settings.siliconflow_api_key
        if not api_key:
            logger.warning("SILICONFLOW_API_KEY is not set. Mem0 initialization deferred.")
            return

        config = {
            "version": "v1.1",
            "llm": {
                "provider": "openai",
                "config": {
                    "model": "deepseek-ai/deepseek-v4.1-flash",
                    "temperature": 0.0,
                    "api_key": api_key,
                    "openai_base_url": "https://api.siliconflow.com/v1",
                    "max_tokens": 1500,
                }
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": "Qwen/Qwen3-Embedding-8B", 
                    "api_key": api_key,
                    "openai_base_url": "https://api.siliconflow.com/v1"
                },
            },
            "vector_store": {"provider": "chroma", "config": {"collection_name": "raphael_memories", "path": "./chroma_db"}},
        }
        try:
            self.memory = Memory.from_config(config)
        except Exception as exc:
            logger.warning("Mem0 initialization failed: %s", exc)
            self.memory = None

    async def process_input(
        self,
        user_id: str,
        text_content: str = None,
        image_bytes: bytes = None,
        audio_bytes: bytes = None,
    ) -> tuple[str, Any]:
        from core.omniscience import get_mini_context, log_message
        from core.llm import _get_llm_client, TOOLS_DEF, SYSTEM_ORCHESTRATOR, SYSTEM_RAPHAEL, query_causal_graph
        from core.llm_tools import (
            update_memory_async, cancel_quest_async, complete_quest_async, create_quest_async,
            manage_user_status_async, update_physical_status_async, manage_project_async,
            manage_capability_async, manage_credits_async, calculate_distance_sync
        )
        from core.search import sparse_search, rerank_chunks
        from core.hud import build_hud
        import json
        import re

        if text_content:
            await log_message(int(user_id), "user", text_content)

        if self.memory is None and settings.siliconflow_api_key:
            self._init_memory()

        mini_ctx = await get_mini_context(int(user_id))
        client = _get_llm_client()

        try:
            from bot.handlers.location import _location_state
            loc_data = _location_state.get(int(user_id))
            h3_index = loc_data["hex"] if loc_data else None
        except ImportError:
            h3_index = None

        async def _add_to_mem0(mem, uid, text):
            if not mem:
                return
            try:
                await asyncio.to_thread(
                    mem.add,
                    messages=[{"role": "user", "content": text}],
                    user_id=uid,
                    metadata={"timestamp": datetime.now().isoformat(), "source": "chat"},
                )
            except Exception as exc:
                logger.warning("Mem0 add failed: %s", exc)

        async def _persist_to_graph(tools_used, uid, h3_idx, chat_text):
            from core.neo4j_client import get_neo4j_driver
            driver = get_neo4j_driver()
            if not driver:
                return
            try:
                if tools_used:
                    event_desc = ", ".join([f"{t.name}: {t.arguments}" for t in tools_used])
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
                
                await asyncio.to_thread(driver.execute_query, query, params)
            except Exception as e:
                logger.warning("Neo4j log error: %s", e)

        # AGENTIC LOOP
        prompt = f"[CONTEXT]\n{mini_ctx}\n[MESSAGE]\n{text_content or ''}"
        messages = [
            {"role": "system", "content": SYSTEM_ORCHESTRATOR},
            {"role": "user", "content": prompt}
        ]

        max_loops = 3
        loop_count = 0
        final_text = ""
        tools_invoked = []

        while loop_count < max_loops:
            loop_count += 1
            try:
                response = await client.chat.completions.create(
                    model="deepseek-ai/deepseek-v4.1-flash",
                    messages=messages,
                    tools=TOOLS_DEF,
                    max_tokens=8000,
                    temperature=0.0
                )
            except Exception as e:
                logger.error(f"Agent Loop LLM Error: {e}")
                final_text = "[Lỗi hệ thống] API DeepSeek gặp sự cố."
                break

            msg = response.choices[0].message
            # OpenAI requires appending the assistant message as is before appending tool results
            msg_dict = {"role": "assistant"}
            if msg.content:
                msg_dict["content"] = msg.content
            if msg.tool_calls:
                msg_dict["tool_calls"] = [{"id": t.id, "type": "function", "function": {"name": t.function.name, "arguments": t.function.arguments}} for t in msg.tool_calls]
            
            messages.append(msg_dict)

            if not msg.tool_calls or msg.content == "TERMINATE_LOOP":
                break

            # Execute Tools
            for tool_call in msg.tool_calls:
                func_name = tool_call.function.name
                tools_invoked.append(tool_call.function)
                try:
                    args = json.loads(tool_call.function.arguments)
                except Exception:
                    args = {}

                tool_result_str = ""

                if func_name == "search_memory_and_causality":
                    q = args.get("query", "")
                    ents = args.get("entities", [])
                    chunks = []
                    
                    # 1. Graph
                    if ents:
                        graph_res = await query_causal_graph(int(user_id), ents)
                        if graph_res: chunks.append(f"[GRAPH]: {graph_res}")
                    
                    # 2. Vector
                    if q:
                        if self.memory:
                            try:
                                mem_res = await asyncio.to_thread(self.memory.search, query=q, user_id=user_id, limit=5)
                                if mem_res:
                                    for m in mem_res: chunks.append(f"[VECTOR]: {m.get('memory', '')}")
                            except Exception as exc:
                                logger.warning("Mem0 search error: %s", exc)
                        
                        # 3. Sparse
                        sparse_res = await sparse_search([q], limit=5)
                        for s in sparse_res: chunks.append(f"[KEYWORD]: {s}")
                    
                    if chunks:
                        reranked = await rerank_chunks(q, chunks, top_k=5)
                        tool_result_str = "\n".join(reranked)
                    else:
                        tool_result_str = "No specific memories found."
                
                # Other Database Tools
                elif func_name == "update_memory":
                    await update_memory_async(int(user_id), args.get("content", ""))
                    tool_result_str = "Memory updated."
                elif func_name == "cancel_quest":
                    await cancel_quest_async(int(user_id), int(args.get("quest_id", 0)), args.get("reason", ""))
                    tool_result_str = "Quest cancelled."
                elif func_name == "complete_quest":
                    await complete_quest_async(int(user_id), int(args.get("quest_id", 0)))
                    tool_result_str = "Quest completed."
                elif func_name == "create_quest":
                    await create_quest_async(int(user_id), args.get("title", ""), args.get("description", ""), args.get("reward", ""), args.get("penalty", ""), int(args.get("parent_quest_id", 0)))
                    tool_result_str = "Quest created."
                elif func_name == "manage_user_status":
                    await manage_user_status_async(int(user_id), args.get("action", ""), args.get("buff_name", ""), args.get("title", ""), int(args.get("expires_in_minutes", 0)))
                    tool_result_str = "Status updated."
                elif func_name == "update_physical_status":
                    await update_physical_status_async(int(user_id), int(args.get("energy", 5)), int(args.get("mood", 5)), int(args.get("health", 5)), float(args.get("sleep_hours", 0)), args.get("notes", ""))
                    tool_result_str = "Physical status updated."
                elif func_name == "manage_project":
                    await manage_project_async(int(user_id), args.get("action", "update"), args.get("name", ""), int(args.get("progress_percent", 0)))
                    tool_result_str = "Project managed."
                elif func_name == "manage_capability":
                    await manage_capability_async(int(user_id), args.get("action", "update"), args.get("domain", ""), float(args.get("level", 0)), float(args.get("exp", 0)), args.get("unit", ""))
                    tool_result_str = "Capability updated."
                elif func_name == "manage_credits":
                    await manage_credits_async(int(user_id), args.get("action", "add"), float(args.get("amount", 0)), args.get("reason", ""))
                    tool_result_str = "Credits updated."
                else:
                    tool_result_str = f"Tool {func_name} executed."

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": tool_result_str
                })

        # Gather Context
        tool_context = []
        for m in messages:
            if m["role"] == "tool":
                tool_context.append(f"<{m.get('name', 'tool')}_data>\n{m.get('content', '')}\n</{m.get('name', 'tool')}_data>")
        context_str = "\n".join(tool_context) if tool_context else "<system_state>No additional DB events.</system_state>"
        
        raphael_prompt = f"""
<sensor_truth>
{context_str}
</sensor_truth>
<chat_history>
{text_content or ''}
</chat_history>
"""
        
        # Second Pass: Persona Synthesis
        try:
            response2 = await client.chat.completions.create(
                model="deepseek-ai/deepseek-v4.1-flash",
                messages=[
                    {"role": "system", "content": SYSTEM_RAPHAEL},
                    {"role": "user", "content": raphael_prompt}
                ],
                max_tokens=8000,
                temperature=0.0,
                extra_body={"reasoning_effort": "high"}
            )
            final_text = response2.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Persona LLM Error: {e}")
            final_text = "[Lỗi hệ thống] API DeepSeek gặp sự cố khi tổng hợp."

        # Strip hidden thinking block from final text before returning to user
        final_text = re.sub(r'<thinking>.*?</thinking>', '', final_text, flags=re.DOTALL).strip()
        final_text = final_text.replace("[Raphael's Voice]", "").strip()

        # Background tasks
        t1 = asyncio.create_task(_persist_to_graph(tools_invoked, int(user_id), h3_index, text_content or ""))
        background_tasks.add(t1)
        t1.add_done_callback(background_tasks.discard)
        
        t2 = asyncio.create_task(_add_to_mem0(self.memory, user_id, text_content or ""))
        background_tasks.add(t2)
        t2.add_done_callback(background_tasks.discard)

        hud_line, keyboard = await build_hud(int(user_id))
        return f"{final_text}\n\n{hud_line}", keyboard


brain = RaphaelBrain()

