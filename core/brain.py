import logging
import asyncio
import json
import re
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
        return_thinking: bool = False,
        on_event: Optional[Any] = None,
    ) -> Any:
        """Run one turn of the Raphael pipeline.

        ``on_event``: optional async callable accepting a ``dict``. When supplied,
        the turn reports progress live (phases, tool timings, reasoning-token
        counts, answer deltas) so an SSE transport can keep the UI continuous
        through the ~15 s of thinking before the first spoken token. The callable
        never receives raw chain-of-thought — only counts and phase labels.
        """
        from core.omniscience import get_mini_context, log_message
        from core.llm import (
            _get_llm_client,
            SYSTEM_ORCHESTRATOR,
            SYSTEM_RAPHAEL,
            TOOLS_DEF,
            WRITE_TOOLS,
            query_causal_graph,
        )
        from core.llm_tools import create_quest_async  # deterministic [QUEST] interception only
        from core.search import sparse_search, rerank_chunks
        from core.hud import build_hud
        import json
        import re
        import time

        turn_started = time.perf_counter()

        def _elapsed_ms() -> int:
            return int((time.perf_counter() - turn_started) * 1000)

        async def _emit(event: dict) -> None:
            """Push a progress event to the transport, never raising into the turn."""
            if on_event is None:
                return
            try:
                await on_event(event)
            except Exception as exc:  # a dead client must not kill the answer
                logger.debug("on_event sink failed: %s", exc)

        await _emit({"type": "phase", "phase": "ingress", "label": "Nhận tri giác", "elapsed_ms": _elapsed_ms()})

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

        await _emit({"type": "phase", "phase": "recall", "label": "Truy xuất ký ức", "elapsed_ms": _elapsed_ms()})

        while loop_count < max_loops:
            loop_count += 1
            await _emit({"type": "loop", "index": loop_count, "status": "start", "elapsed_ms": _elapsed_ms()})
            loop_started = time.perf_counter()
            try:
                response = await client.chat.completions.create(
                    model=settings.deepseek_model,
                    messages=messages,
                    tools=TOOLS_DEF,
                    max_tokens=settings.deepseek_orchestrator_max_tokens,
                    temperature=0.0,
                    extra_body={"thinking": {"type": "disabled"}}
                )
            except Exception as e:
                logger.error(f"Agent Loop LLM Error: {e}")
                final_text = "[Lỗi hệ thống] API DeepSeek gặp sự cố."
                break

            decide_ms = int((time.perf_counter() - loop_started) * 1000)
            msg = response.choices[0].message
            # OpenAI requires appending the assistant message as is before appending tool results
            msg_dict = {"role": "assistant"}
            if msg.content:
                msg_dict["content"] = msg.content
            if msg.tool_calls:
                msg_dict["tool_calls"] = [{"id": t.id, "type": "function", "function": {"name": t.function.name, "arguments": t.function.arguments}} for t in msg.tool_calls]
            
            messages.append(msg_dict)
            await _emit({
                "type": "loop",
                "index": loop_count,
                "status": "decided",
                "decide_ms": decide_ms,
                "tool_calls": len(msg.tool_calls or []),
                "elapsed_ms": _elapsed_ms(),
            })

            if not msg.tool_calls or msg.content == "TERMINATE_LOOP":
                break

            # --- State-write turn ------------------------------------------------
            # The write loop is *thinking*, not bookkeeping: this system decides
            # what to record about Master (energy, quests, credits) as part of
            # reasoning, so it must stay an orchestrator turn. What it must not do
            # is sit in front of the answer. When a turn asks for nothing but
            # writes, dispatch them and start Pass 2 immediately — they land while
            # the persona is being written.
            write_only = all(tc.function.name in WRITE_TOOLS for tc in msg.tool_calls)
            if write_only and settings.deepseek_defer_writes:
                dispatched = []
                for tool_call in msg.tool_calls:
                    tools_invoked.append(tool_call.function)
                    try:
                        args = json.loads(tool_call.function.arguments)
                    except Exception:
                        args = {}
                    dispatched.append(tool_call.function.name)
                    task = asyncio.create_task(_apply_write(tool_call.function.name, args, int(user_id)))
                    background_tasks.add(task)
                    task.add_done_callback(background_tasks.discard)
                await _emit({
                    "type": "tool",
                    "name": ", ".join(dispatched),
                    "status": "async",
                    "count": len(dispatched),
                    "elapsed_ms": _elapsed_ms(),
                })
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
                tool_started = time.perf_counter()

                if func_name in WRITE_TOOLS:
                    # Mixed read+write turn: the loop is still gathering, so the
                    # write runs inline (original behaviour) and its 6-token
                    # confirmation joins sensor_truth.
                    tool_result_str = await _apply_write(func_name, args, int(user_id))
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": func_name,
                        "content": tool_result_str,
                    })
                    await _emit({
                        "type": "tool",
                        "name": func_name,
                        "status": "done",
                        "ms": int((time.perf_counter() - tool_started) * 1000),
                        "elapsed_ms": _elapsed_ms(),
                    })
                    continue

                if func_name == "search_memory_and_causality":
                    q = args.get("query", "")
                    ents = args.get("entities", [])
                    chunks = []
                    
                    # 1. Graph
                    if ents:
                        graph_res = await query_causal_graph(int(user_id), ents)
                        if graph_res: chunks.append(f"[GRAPH]: {graph_res}")
                        try:
                            from core.gds_service import GDSService
                            gds_ctx = await GDSService.synthesize_gds_context(int(user_id), ents)
                            if gds_ctx:
                                chunks.append(f"[GDS STRUCTURAL INSIGHT]: {gds_ctx}")
                        except Exception as exc:
                            logger.debug("GDS synthesis in search error: %s", exc)
                    
                    # 2. Vector
                    if q:
                        if self.memory:
                            try:
                                try:
                                    mem_res = await asyncio.to_thread(self.memory.search, query=q, filters={"user_id": user_id}, limit=5)
                                except TypeError:
                                    mem_res = await asyncio.to_thread(self.memory.search, query=q, user_id=user_id, limit=5)
                                if mem_res:
                                    for m in mem_res:
                                        m_text = m.get("memory", str(m)) if isinstance(m, dict) else str(m)
                                        chunks.append(f"[VECTOR]: {m_text}")
                            except Exception as exc:
                                logger.warning("Mem0 search error: %s", exc)
                        
                        # 3. Sparse
                        sparse_res = await sparse_search([q], limit=5)
                        for s in sparse_res: chunks.append(f"[KEYWORD]: {s}")
                    
                    if chunks:
                        reranked = await rerank_chunks(q, chunks, top_k=8)
                        try:
                            from core.gds_service import rerank_chunks_with_pagerank
                            struct_reranked = await rerank_chunks_with_pagerank(int(user_id), reranked, top_k=5)
                            tool_result_str = "\n".join(struct_reranked)
                        except Exception:
                            tool_result_str = "\n".join(reranked[:5])
                    else:
                        tool_result_str = "No specific memories found."

                elif func_name == "analyze_graph_data_science":
                    try:
                        from core.gds_service import GDSService
                        algo = args.get("algorithm", "pagerank")
                        src = args.get("source_node", "")
                        tgt = args.get("target_node", "")
                        
                        if algo == "pagerank":
                            nodes = await GDSService.get_global_pagerank(int(user_id), limit=5)
                            lines = [f"- '{n['name']}' ({n['type']}): Centrality Score {n['score']}" for n in nodes]
                            tool_result_str = "[GDS PAGERANK (Root Causal Centrality)]:\n" + ("\n".join(lines) if lines else "No central nodes found.")
                        elif algo == "personalized_pagerank":
                            ripple = await GDSService.get_personalized_pagerank(int(user_id), src, limit=5)
                            lines = [f"- '{r['name']}' ({r['type']}): Ripple Impact {r['score']}" for r in ripple]
                            tool_result_str = f"[GDS PERSONALIZED PAGERANK (Ripple from '{src}')]:\n" + ("\n".join(lines) if lines else f"No ripple effect detected from '{src}'.")
                        elif algo == "betweenness":
                            bns = await GDSService.get_critical_bottlenecks(int(user_id), limit=5)
                            lines = [f"- '{b['name']}' ({b['type']}): Bottleneck Score {b['score']}" for b in bns]
                            tool_result_str = "[GDS BETWEENNESS (Systemic Bottlenecks & Vulnerabilities)]:\n" + ("\n".join(lines) if lines else "No bottlenecks found.")
                        elif algo == "louvain":
                            comms = await GDSService.detect_causal_communities(int(user_id), limit=4)
                            lines = [f"- {cluster}: {', '.join(members)}" for cluster, members in comms.items()]
                            tool_result_str = "[GDS LOUVAIN (Causal Communities)]:\n" + ("\n".join(lines) if lines else "No distinct clusters detected.")
                        elif algo == "shortest_path":
                            path = await GDSService.find_causal_shortest_path(int(user_id), src, tgt)
                            tool_result_str = f"[GDS CAUSAL PATH ('{src}' -> '{tgt}')]:\n" + (" -> ".join(path) if path else f"No direct path found between '{src}' and '{tgt}'.")
                        else:
                            tool_result_str = f"Algorithm '{algo}' not supported."
                    except Exception as e:
                        logger.warning("GDS tool error: %s", e)
                        tool_result_str = f"[GDS ERROR]: {e}"
                
                # Write tools are intercepted above and never reach this dispatch;
                # an unknown name is a read-tool contract violation, not an action.
                elif func_name == "calculate_distance":
                    from core.llm_tools import calculate_distance_sync
                    tool_result_str = calculate_distance_sync(
                        float(args.get("lat1", 0.0)),
                        float(args.get("lon1", 0.0)),
                        float(args.get("lat2", 0.0)),
                        float(args.get("lon2", 0.0)),
                    )
                else:
                    tool_result_str = f"[UNSUPPORTED] Read tool '{func_name}' is not available in the reasoning loop."

                await _emit({
                    "type": "tool",
                    "name": func_name,
                    "status": "done",
                    "ms": int((time.perf_counter() - tool_started) * 1000),
                    "result_tokens": len(tool_result_str) // 4,
                    "elapsed_ms": _elapsed_ms(),
                })

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

        # Ensure GDS Structural Causal Insight is ALWAYS present in sensor_truth
        has_gds = any("gds" in m.lower() for m in tool_context)
        if not has_gds:
            try:
                from core.gds_service import GDSService
                candidates = ["TS. Hùng", "Đồ án STM32", "Board STM32 bị nổ", "Nam", "Game Valorant", "STM32"]
                matched_ents = [c for c in candidates if c.lower() in (text_content or "").lower()]
                gds_context = await GDSService.synthesize_gds_context(int(user_id), entities=matched_ents or None)
                if gds_context:
                    tool_context.append(f"<gds_causal_topology>\n{gds_context}\n</gds_causal_topology>")
            except Exception as exc:
                logger.debug("Auto GDS synthesis error: %s", exc)

        context_str = "\n".join(tool_context) if tool_context else "<system_state>No additional DB events.</system_state>"
        
        raphael_prompt = f"""
<sensor_truth>
{context_str}
</sensor_truth>
<chat_history>
{text_content or ''}
</chat_history>

<CRITICAL_RULE>
- MANDATORY THINKING REQUIREMENT: You MUST perform deep causal and psychological reasoning inside your <thinking>...</thinking> block.
  1. GDS Topological Cross-Reference: Explicitly analyze the GDS structural graph insights (<gds_causal_topology> or <gds_structural_graph_analysis>) if provided: root causes (PageRank), systemic bottleneck bridges (Betweenness Centrality), and community clustering (Louvain).
  2. Psychological & Biological Realism: Analyze Master's hidden motives (e.g. escapism into gaming vs displaced aggression towards roommate Nam), cortisol / biological exhaustion, and why multiple crises converge.
  3. Action Triage: Determine the exact priority delta (P0 immediate biological survival vs P1 academic negotiation vs P2 interpersonal conflict).
- THINKING_BUDGET: ULTRA-CONCISE. Limit thinking inside <thinking> to at most 100-150 words (~100-200 tokens). Analyze GDS topology and P0 biological triage directly without verbose internal monologue.
- CONTENT_FOCUS: Insight given is insight rejected! ALL deep psychological and GDS causal analysis MUST be completely hidden inside the <thinking> block. The final output to the user must be brief, calm, and direct.
- OUTPUT_FORMAT: AFTER </thinking>, the spoken response must be EXTREMELY SHORT (MAXIMUM 1-2 SENTENCES). Begin with standard prefix: 《Báo cáo》, 《Giải đáp》, 《Xác nhận》, or 《Phủ định》.
- PRONOUNS: Use ONLY "Ngài" or "Master" for the user. Use ONLY "tôi" for yourself. NEVER use "ta", "mình", "người dùng", "bạn".
- TONE: Sentient, elegantly polite, deeply loyal. Speak directly without unnecessary fluff.
</CRITICAL_RULE>
"""
        
        # Second Pass: Persona Synthesis
        await _emit({"type": "phase", "phase": "reasoning", "label": "Suy luận nhân quả", "elapsed_ms": _elapsed_ms()})
        try:
            if settings.deepseek_reasoning_effort.lower() in ("none", "disabled", "off"):
                pass2_extra = {"thinking": {"type": "disabled"}}
            else:
                pass2_extra = {"reasoning_effort": settings.deepseek_reasoning_effort}

            pass2_messages = [
                {"role": "system", "content": SYSTEM_RAPHAEL},
                {"role": "user", "content": raphael_prompt}
            ]

            if on_event is None:
                response2 = await client.chat.completions.create(
                    model=settings.deepseek_model,
                    messages=pass2_messages,
                    max_tokens=settings.deepseek_max_tokens,
                    temperature=0.0,
                    extra_body=pass2_extra
                )
                msg2 = response2.choices[0].message
                final_text = msg2.content or ""
                reasoning_text = getattr(msg2, "reasoning_content", None) or ""
            else:
                # Streaming transport: reasoning streams first as `reasoning_content`,
                # then the spoken answer as `content`. Only the answer may be shown;
                # reasoning is counted and timed, never forwarded (Insight given is
                # insight rejected).
                stream = await client.chat.completions.create(
                    model=settings.deepseek_model,
                    messages=pass2_messages,
                    max_tokens=settings.deepseek_max_tokens,
                    temperature=0.0,
                    stream=True,
                    extra_body=pass2_extra
                )
                final_text = ""
                reasoning_text = ""
                reasoning_chars = 0
                spoken_chars = 0
                last_progress = time.monotonic()

                async for chunk in stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    piece = getattr(delta, "reasoning_content", None)
                    if piece:
                        reasoning_text += piece
                        reasoning_chars += len(piece)
                        now = time.monotonic()
                        if now - last_progress >= 0.25:
                            last_progress = now
                            await _emit({
                                "type": "reasoning",
                                "tokens": reasoning_chars // 4,
                                "elapsed_ms": _elapsed_ms(),
                            })
                        continue
                    piece = getattr(delta, "content", None)
                    if piece:
                        final_text += piece
                        spoken_chars += len(piece)
                        await _emit({"type": "token", "text": piece, "token": piece, "response": piece})

                await _emit({
                    "type": "reasoning",
                    "tokens": reasoning_chars // 4,
                    "spoken_tokens": spoken_chars // 4,
                    "final": True,
                    "elapsed_ms": _elapsed_ms(),
                })

            # Check if thinking was enclosed in <thinking> inside final_text
            thinking_match = re.search(r'<thinking>(.*?)</thinking>', final_text, flags=re.DOTALL)
            if thinking_match:
                if not reasoning_text:
                    reasoning_text = thinking_match.group(1).strip()
                final_text = re.sub(r'<thinking>.*?</thinking>', '', final_text, flags=re.DOTALL).strip()
        except Exception as e:
            logger.error(f"Persona LLM Error: {e}")
            final_text = "[Lỗi hệ thống] API DeepSeek gặp sự cố khi tổng hợp."
            reasoning_text = ""

        # Build unstripped_text containing thinking for Metacognition (SQLite, Mem0, Neo4j)
        if reasoning_text:
            unstripped_text = f"<thinking>\n{reasoning_text}\n</thinking>\n{final_text}"
        else:
            unstripped_text = final_text

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
        full_res = f"{final_text}\n\n{hud_line}"
        if return_thinking:
            return full_res, keyboard, reasoning_text
        return full_res, keyboard


# ---------------------------------------------------------------------------
# State-write path
# ---------------------------------------------------------------------------
# The write *decision* stays inside the orchestrator loop (it is reasoning about
# what to record about Master). Only the *execution* may be moved: when a turn
# asks for nothing but writes, they are dispatched as background tasks so they
# land while Pass 2 is writing the answer.

async def _apply_write(func_name: str, args: dict, user_id: int) -> str:
    """Execute exactly one state-mutating tool. Never raises."""
    from core.llm_tools import (
        cancel_quest_async,
        complete_quest_async,
        create_quest_async,
        manage_user_status_async,
        update_physical_status_async,
        manage_project_async,
        manage_capability_async,
        manage_credits_async,
    )

    try:
        if func_name == "ingest_knowledge":
            text_content = args.get("text_content", "")
            if not text_content:
                return "[ERROR] Thiếu nội dung để nạp."
            import subprocess
            import uuid
            import os
            os.makedirs("scratch", exist_ok=True)
            temp_filename = f"scratch/temp_ingest_{uuid.uuid4().hex[:8]}.txt"
            with open(temp_filename, "w", encoding="utf-8") as tf:
                tf.write(text_content)
            subprocess.Popen(["python", "scripts/ingest_text.py", temp_filename])
            return "[SUCCESS] Đã khởi chạy tiến trình nạp dữ liệu thô vào GraphRAG."

        if func_name == "cancel_quest":
            await cancel_quest_async(user_id, int(args.get("quest_id", 0)), args.get("reason", ""))
            return "Quest cancelled."
        if func_name == "complete_quest":
            await complete_quest_async(user_id, int(args.get("quest_id", 0)))
            return "Quest completed."
        if func_name == "create_quest":
            await create_quest_async(
                user_id,
                args.get("title", ""),
                args.get("description", ""),
                args.get("reward", ""),
                args.get("penalty", ""),
                int(args.get("parent_quest_id", 0)),
            )
            return "Quest created."
        if func_name == "manage_user_status":
            await manage_user_status_async(
                user_id,
                args.get("action", ""),
                args.get("buff_name", ""),
                args.get("title", ""),
                int(args.get("expires_in_minutes", 0)),
            )
            return "Status updated."
        if func_name == "update_physical_status":
            await update_physical_status_async(
                user_id,
                int(args.get("energy", 5)),
                int(args.get("mood", 5)),
                int(args.get("health", 5)),
                float(args.get("sleep_hours", 0)),
                args.get("notes", ""),
            )
            return "Physical status updated."
        if func_name == "manage_project":
            await manage_project_async(
                user_id,
                args.get("action", "update"),
                args.get("name", ""),
                int(args.get("progress_percent", 0)),
            )
            return "Project managed."
        if func_name == "manage_capability":
            await manage_capability_async(
                user_id,
                args.get("action", "update"),
                args.get("domain", ""),
                float(args.get("level", 0)),
                float(args.get("exp", 0)),
                args.get("unit", ""),
            )
            return "Capability updated."
        if func_name == "manage_credits":
            await manage_credits_async(
                user_id, args.get("action", "add"), float(args.get("amount", 0)), args.get("reason", "")
            )
            return "Credits updated."
        return f"[SKIPPED] Unknown write tool '{func_name}'."
    except Exception as exc:
        logger.warning("Write tool %s failed: %s", func_name, exc)
        return f"[ERROR] {func_name}: {exc}"


brain = RaphaelBrain()

