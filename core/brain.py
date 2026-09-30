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

        llm_api_key = settings.deepseek_api_key or settings.siliconflow_api_key
        llm_base_url = settings.deepseek_base_url if settings.deepseek_api_key else "https://api.siliconflow.com/v1"
        llm_model = settings.deepseek_model if settings.deepseek_api_key else "deepseek-ai/deepseek-v4.1-flash"

        config = {
            "version": "v1.1",
            "llm": {
                "provider": "openai",
                "config": {
                    "model": llm_model,
                    "temperature": 0.0,
                    "api_key": llm_api_key,
                    "openai_base_url": llm_base_url,
                    "max_tokens": 1500,
                }
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": "Qwen/Qwen3-Embedding-8B", 
                    "api_key": settings.siliconflow_api_key,
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
            cancel_quest_async, complete_quest_async, create_quest_async,
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

        async def _add_to_mem0(mem, uid, text, h3_idx=""): 
            if not mem:
                return
            try:
                await asyncio.to_thread(
                    mem.add,
                    messages=[{"role": "user", "content": text}],
                    user_id=uid,
                    metadata={"timestamp": datetime.now().isoformat(), "source": "chat", "h3_index": str(h3_idx or "")},
                )
            except Exception as exc:
                logger.warning("Mem0 add failed: %s", exc)

        async def _persist_to_graph(tools_used, uid, h3_idx, chat_text):
            from core.neo4j_client import get_neo4j_driver
            from core.llm import get_ai_response
            from core.llm_tools import create_quest_async
            import json
            import re
            
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
                    
                from core.ontology_prompt import ONTOLOGY_PROMPT_TEMPLATE
                extraction_prompt = f"""{ONTOLOGY_PROMPT_TEMPLATE}
[NỘI DUNG CẦN BÓC TÁCH]
{event_desc}"""
                response = await get_ai_response(extraction_prompt, model=settings.deepseek_model, temperature=0.0)
                
                json_match = re.search(r'\{.*\}', response.replace('\n', ''), re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                else:
                    data = json.loads(response)
                
                # 1. Bóc tách SQLite Quests
                quests = data.get("sqlite_quests", [])
                for q in quests:
                    try:
                        await create_quest_async(
                            user_id=uid,
                            title=q.get("title", "Nhiệm vụ Ẩn"),
                            description=q.get("description", ""),
                            reward=q.get("reward", "10 XP"),
                            penalty=q.get("penalty", "-10 HP")
                        )
                    except Exception as q_err:
                        pass
                        
                # 2. Bóc tách Neo4j Graph
                neo4j_data = data.get("neo4j", data) # Fallback to old format if 'neo4j' key missing
                async with driver.session() as session:
                    await session.run("MERGE (u:User {telegram_id: $uid, id: $uid})", uid=uid)
                    
                    for node in neo4j_data.get("nodes", []):
                        label, name = node.get("label"), node.get("name")
                        if label and name:
                            props = {k: v for k, v in node.items() if k not in ["label", "name"]}
                            props.setdefault("timestamp", datetime.now().isoformat())
                            props.setdefault("h3_index", h3_idx)
                            prop_str = ", ".join([f"n.{k} = ${k}" for k in props.keys()])
                            query = f"MERGE (n:{label} {{name: $name}})"
                            if prop_str:
                                query += f" SET {prop_str}"
                            await session.run(query, name=name, **props)
                            await session.run(f"MATCH (u:User {{id: $uid}}), (n:{label} {{name: $name}}) MERGE (u)-[:EXPERIENCED]->(n)", uid=uid, name=name)
                            
                    # Support 'relationships' schema from ontology_prompt.py
                    for rel in neo4j_data.get("relationships", []):
                        s_label = rel.get("source_label")
                        s_name = rel.get("source_name")
                        t_label = rel.get("target_label")
                        t_name = rel.get("target_name")
                        r_type = rel.get("type", "RELATED_TO")
                        if s_label and s_name and t_label and t_name and r_type:
                            query = f"MATCH (a:{s_label} {{name: $s_name}}), (b:{t_label} {{name: $t_name}}) MERGE (a)-[:{r_type}]->(b)"
                            await session.run(query, src_name=s_name, tgt_name=t_name)
                        elif rel.get("source") and rel.get("target"):
                            src_id, tgt_id = rel.get("source"), rel.get("target")
                            src_node = next((n for n in neo4j_data.get("nodes", []) if n.get("id") == src_id), None)
                            tgt_node = next((n for n in neo4j_data.get("nodes", []) if n.get("id") == tgt_id), None)
                            if src_node and tgt_node:
                                query = f"MATCH (a:{src_node['label']} {{name: $src_name}}), (b:{tgt_node['label']} {{name: $tgt_name}}) MERGE (a)-[:{r_type}]->(b)"
                                await session.run(query, src_name=src_node['name'], tgt_name=tgt_node['name'])

                    # Support legacy 'edges' schema
                    for edge in neo4j_data.get("edges", []):
                        src_id, tgt_id, rel = edge.get("source"), edge.get("target"), edge.get("type", "RELATED_TO")
                        src_node = next((n for n in neo4j_data.get("nodes", []) if n.get("id") == src_id), None)
                        tgt_node = next((n for n in neo4j_data.get("nodes", []) if n.get("id") == tgt_id), None)
                        if src_node and tgt_node:
                            query = f"MATCH (a:{src_node['label']} {{name: $src_name}}), (b:{tgt_node['label']} {{name: $tgt_name}}) MERGE (a)-[:{rel}]->(b)"
                            await session.run(query, src_name=src_node['name'], tgt_name=tgt_node['name'])
            except Exception as e:
                logger.warning("Graph/Quest extraction error: %s", e)

        # AGENTIC LOOP
        base_prompt_text = f"""[CONTEXT]
{mini_ctx}
[MESSAGE]
{text_content or ''}"""
        
        user_content = [{"type": "text", "text": base_prompt_text}]
        if image_bytes:
            import base64
            img_b64 = base64.b64encode(image_bytes).decode("utf-8")
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
            })

        messages = [
            {"role": "system", "content": SYSTEM_ORCHESTRATOR},
            {"role": "user", "content": user_content}
        ]

        max_loops = 3
        loop_count = 0
        final_text = ""
        tools_invoked = []

        while loop_count < max_loops:
            loop_count += 1
            try:
                response = await client.chat.completions.create(
                    model=settings.deepseek_model,
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

                if func_name == "ingest_knowledge":
                    text_content = args.get("text_content", "")
                    if text_content:
                        import subprocess
                        import uuid
                        import os
                        os.makedirs("scratch", exist_ok=True)
                        temp_filename = f"scratch/temp_ingest_{uuid.uuid4().hex[:8]}.txt"
                        with open(temp_filename, "w", encoding="utf-8") as tf:
                            tf.write(text_content)
                        # Spawn background process so it doesn't block the chat
                        subprocess.Popen(["python", "scripts/ingest_text.py", temp_filename])
                        tool_result_str = "[SUCCESS] Đã khởi chạy tiến trình chạy ngầm (Background Task) để nạp dữ liệu thô vào GraphRAG. Tiến trình sẽ hoàn tất trong vài chục giây."
                    else:
                        tool_result_str = "[ERROR] Thiếu nội dung để nạp."

                elif func_name == "search_memory_and_causality":
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
                                try:
                                    mem_res = await asyncio.to_thread(self.memory.search, query=q, filters={"user_id": user_id}, limit=5)
                                except TypeError:
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

<CRITICAL_RULE>
- OUTPUT_FORMAT: EXTREMELY SHORT. MAXIMUM 1-2 SENTENCES. Do NOT write paragraphs.
- CONTENT_FOCUS: Insight given is insight rejected! ALL deep psychological analysis MUST be completely hidden inside the <thinking> block. The final output to the user must be brief, calm, and direct.
- PRONOUNS: Use ONLY "Ngài" or "Master" for the user. Use ONLY "tôi" for yourself. NEVER use "ta", "mình", "người dùng", "bạn".
- TONE: Sentient, elegantly polite, deeply loyal. Speak directly without unnecessary fluff.
</CRITICAL_RULE>
"""
        
        # Second Pass: Persona Synthesis
        try:
            response2 = await client.chat.completions.create(
                model=settings.deepseek_model,
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

        # Cache the thinking block to DB so the assistant can remember its rationale
        unstripped_text = final_text
        # Strip hidden thinking block from final text before returning to user
        final_text = re.sub(r'<thinking>.*?</thinking>', '', final_text, flags=re.DOTALL).strip()
        
        # Background task to log the assistant's FULL response (with thinking) to SQLite
        t0 = asyncio.create_task(log_message(int(user_id), "assistant", unstripped_text))
        background_tasks.add(t0)
        t0.add_done_callback(background_tasks.discard)
        final_text = final_text.replace("[Raphael's Voice]", "").strip()


        # Intercept and process Side Quests
        quest_match = re.search(r'\[QUEST\](.*?)\|\s*Reward:(.*?)(?:\|\s*Penalty:(.*?))?(?:\|\s*Expire:(.*?))?(?:\|\s*Proof:(.*))?$', final_text)
        if quest_match:
            q_title = quest_match.group(1).strip()
            q_reward = quest_match.group(2).strip()
            q_penalty = (quest_match.group(3) or "Không").strip()
            q_expire_str = (quest_match.group(4) or "60").strip()
            q_proof = (quest_match.group(5) or "tự do").strip()
            
            exp_mins = 60
            m = re.search(r'\d+', q_expire_str)
            if m:
                exp_mins = int(m.group())
            
            t_q = asyncio.create_task(create_quest_async(int(user_id), q_title, "Auto-generated by Raphael", q_reward, q_penalty, expires_in_minutes=exp_mins, proof_required=q_proof))
            background_tasks.add(t_q)
            t_q.add_done_callback(background_tasks.discard)
            
            penalty_display = f" | Phạt: {q_penalty}" if q_penalty and q_penalty.lower() not in ["không", "none", "no", "0"] else ""
            final_text = re.sub(r'\[QUEST\].*', f'🔥 **NHIỆM VỤ MỚI:** {q_title} (Thưởng: {q_reward}{penalty_display})\n_Đã đồng bộ vào /quests_', final_text)

        # Background tasks - Injects both User's input and AI's metacognitive thought process into the 3-DB ecosystem

        combined_memory_string = f"User Input: {text_content or ''}\nAI Thought Process: {unstripped_text}"
        
        t1 = asyncio.create_task(_persist_to_graph(tools_invoked, int(user_id), h3_index, combined_memory_string))
        background_tasks.add(t1)
        t1.add_done_callback(background_tasks.discard)
        
        t2 = asyncio.create_task(_add_to_mem0(self.memory, user_id, combined_memory_string, h3_index))
        background_tasks.add(t2)
        t2.add_done_callback(background_tasks.discard)

        hud_line, keyboard = await build_hud(int(user_id))
        return f"{final_text}\n\n{hud_line}", keyboard


brain = RaphaelBrain()

