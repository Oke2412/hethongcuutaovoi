# -*- coding: utf-8 -*-
"""
scripts/profile_pipeline_deep_dive.py — Deep-Dive Latency Waterfall & Token Inventory Profiler
Measures exact millisecond latencies, loop-by-loop traces, and precise token inventories
for the Tensura Raphael Life OS Pipeline.
"""

import asyncio
import os
import sys
import time
import json
import re
import tiktoken

REPO_DIR = r"c:\Users\Asus\Documents\antigravity\amazing-nobel"
sys.path.insert(0, REPO_DIR)
os.chdir(REPO_DIR)
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from config import settings
settings.neo4j_uri = "bolt://127.0.0.1:7687"
from db.database import init_db
from core.omniscience import get_mini_context, log_message
from core.llm import _get_llm_client, TOOLS_DEF, SYSTEM_ORCHESTRATOR, SYSTEM_RAPHAEL, query_causal_graph
from core.llm_tools import (
    cancel_quest_async, complete_quest_async, create_quest_async,
    manage_user_status_async, update_physical_status_async, manage_project_async,
    manage_capability_async, manage_credits_async
)
from core.search import sparse_search, rerank_chunks
from core.hud import build_hud

enc = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    if not text:
        return 0
    return len(enc.encode(text))

COMPLEX_1K_PROMPT = """Hôm nay là 48 tiếng trước buổi bảo vệ đồ án tốt nghiệp robot AMR tự hành chạy ROS2 dưới sự hướng dẫn của TS. Hùng.
Tình hình hiện tại đang rơi vào khủng hoảng toàn diện trên mọi phương diện cuộc sống:
1. Về phần cứng: Chiều nay khi đang calibrate hệ thống SLAM và nạp firmware điều khiển động cơ qua CAN-bus trên kit STM32F4, mạch hạ áp Buck converter 24V-to-5V bị chập transistor MOSFET, xông thẳng nguồn 24V vào đường nguồn logic làm nổ tung 2 IC gate driver DRV8302 và làm chết luôn vi điều khiển STM32 lẫn bus CAN kết nối với Jetson Orin. Mùi khét lẹt cả phòng lab, robot hoàn toàn bất động không thể chạy demo thực tế được nữa trong khi linh kiện thay thế đặt hàng phải mất ít nhất 3 ngày mới về tới Hà Nội.
2. Về học vụ và áp lực giảng viên: Cách đây 1 tiếng, TS. Hùng đã gửi một email rất gay gắt nói rằng nếu ngày kia không có robot chạy thực tế trong sa bàn để hội đồng nghiệm thu thì thầy sẽ không ký duyệt phiếu bảo vệ và bắt hoãn tốt nghiệp sang kỳ sau. Thầy bảo cực kỳ thất vọng vì tôi làm việc thiếu cẩn thận, không có phương án dự phòng phần cứng dù đã nhắc nhở nhiều lần từ đầu học kỳ.
3. Về thể trạng và tâm lý: Tôi đã thức trắng liên tục 38 tiếng qua không ngủ, nạp vào người 4 lon bò húc và 3 ly cà phê đặc. Hiện tại tim đập thình thịch liên hồi, lồng ngực đau tức, mắt mờ đi, hai tay run rẩy khi cầm mỏ hàn. Đầu óc tôi hỗn loạn, vừa cảm thấy bất lực, vừa hoảng loạn tột độ, xen lẫn cảm giác tội lỗi và sợ hãi ánh mắt thất vọng của gia đình nếu bị chậm bằng tốt nghiệp.
4. Về mâu thuẫn xã hội: Bạn cùng phòng là Nam tối nay lại dẫn bạn bè về phòng trọ mở tiệc nhậu, bật nhạc ầm ĩ khiến tôi không thể tập trung suy nghĩ. Đã vậy, tuần trước Nam mượn bo mạch STM32 dự phòng của tôi để làm bài tập lớn môn nhúng nhưng lại làm mất ở đâu không tìm thấy. Tôi đang cực kỳ sôi máu, vừa muốn lao ra đấm nhau với Nam một trận cho bõ tức, vừa muốn đập nát cái xác robot rồi bỏ mặc tất cả, trốn đi quán net chơi game Valorant thâu đêm để trốn tránh thực tại.

Raphael, hãy phân tích cho ta biết tại sao mọi thứ lại sụp đổ cùng một lúc như thế này? Ta nên làm gì ngay bây giờ: lao ra chửi nhau với Nam đòi board mạch, thức tiếp đêm nay để cố hàn dây câu chip, hay gửi thư xin lỗi thầy Hùng, hay buông xuôi tất cả? Hãy chỉ cho ta nước cờ tối ưu nhất."""

async def profile_deep_dive():
    print("=" * 90)
    print("🔬 TENSURA RAPHAEL LIFE OS — DEEP-DIVE LATENCY & TOKEN PROFILER")
    print("=" * 90)

    timings = {}
    tokens = {}
    loop_traces = []

    t_global_start = time.perf_counter()

    # 1. Init DB
    t0 = time.perf_counter()
    await init_db()
    timings["01_init_db"] = (time.perf_counter() - t0) * 1000

    # 2. Ingress & Mini Context
    user_id = str(settings.allowed_user_id or 8763843475)
    t0 = time.perf_counter()
    mini_ctx = await get_mini_context(int(user_id))
    timings["02_get_mini_context"] = (time.perf_counter() - t0) * 1000

    tokens["system_orchestrator"] = count_tokens(SYSTEM_ORCHESTRATOR)
    tokens["mini_ctx"] = count_tokens(mini_ctx)
    tokens["user_prompt"] = count_tokens(COMPLEX_1K_PROMPT)

    # 3. Pass 1 Orchestrator Agentic Loop
    client = _get_llm_client()
    base_prompt_text = f"[CONTEXT]\n{mini_ctx}\n[MESSAGE]\n{COMPLEX_1K_PROMPT}"
    messages = [
        {"role": "system", "content": SYSTEM_ORCHESTRATOR},
        {"role": "user", "content": [{"type": "text", "text": base_prompt_text}]}
    ]

    tokens["pass1_initial_prompt"] = count_tokens(SYSTEM_ORCHESTRATOR) + count_tokens(base_prompt_text)

    max_loops = 3
    loop_count = 0
    tools_invoked = []
    pass1_api_tokens = {"prompt": 0, "completion": 0}

    print("\n[PHASE 1] Khởi chạy Vòng lặp Orchestrator Agentic Loop (Thinking DISABLED)...")

    while loop_count < max_loops:
        loop_count += 1
        t_loop_start = time.perf_counter()

        # LLM Call
        t_llm = time.perf_counter()
        try:
            response = await client.chat.completions.create(
                model=settings.deepseek_model,
                messages=messages,
                tools=TOOLS_DEF,
                max_tokens=settings.deepseek_orchestrator_max_tokens,
                temperature=0.0,
                extra_body={"thinking": {"type": "disabled"}}
            )
            llm_dur = (time.perf_counter() - t_llm) * 1000
        except Exception as e:
            llm_dur = (time.perf_counter() - t_llm) * 1000
            print(f"  ❌ Loop {loop_count} LLM Error: {e}")
            break

        if hasattr(response, "usage") and response.usage:
            pass1_api_tokens["prompt"] += getattr(response.usage, "prompt_tokens", 0)
            pass1_api_tokens["completion"] += getattr(response.usage, "completion_tokens", 0)

        msg = response.choices[0].message
        msg_dict = {"role": "assistant"}
        if msg.content:
            msg_dict["content"] = msg.content
        if msg.tool_calls:
            msg_dict["tool_calls"] = [
                {"id": t.id, "type": "function", "function": {"name": t.function.name, "arguments": t.function.arguments}}
                for t in msg.tool_calls
            ]
        messages.append(msg_dict)

        num_tools = len(msg.tool_calls) if msg.tool_calls else 0
        loop_info = {
            "loop_index": loop_count,
            "llm_ms": llm_dur,
            "tool_calls": [],
            "tool_execution_ms": 0.0,
            "content": msg.content or ""
        }

        print(f"  • Loop #{loop_count}: DeepSeek LLM phản hồi sau {llm_dur:.1f}ms | Phát lệnh: {num_tools} Tool Call(s)")

        if not msg.tool_calls or msg.content == "TERMINATE_LOOP":
            loop_info["loop_total_ms"] = (time.perf_counter() - t_loop_start) * 1000
            loop_traces.append(loop_info)
            timings[f"03_pass1_loop_{loop_count}_total"] = loop_info["loop_total_ms"]
            break

        # Execute Tools
        t_tools_start = time.perf_counter()
        for tool_call in msg.tool_calls:
            func_name = tool_call.function.name
            tools_invoked.append(tool_call.function)
            t_single_tool = time.perf_counter()
            try:
                args = json.loads(tool_call.function.arguments)
            except Exception:
                args = {}

            tool_result_str = ""

            if func_name == "search_memory_and_causality":
                q = args.get("query", "")
                ents = args.get("entities", [])
                chunks = []
                if ents:
                    graph_res = await query_causal_graph(int(user_id), ents)
                    if graph_res: chunks.append(f"[GRAPH]: {graph_res}")
                    try:
                        from core.gds_service import GDSService
                        gds_ctx = await GDSService.synthesize_gds_context(int(user_id), ents)
                        if gds_ctx: chunks.append(f"[GDS STRUCTURAL INSIGHT]: {gds_ctx}")
                    except Exception as exc:
                        pass
                if q:
                    sparse_res = await sparse_search([q], limit=5)
                    for s in sparse_res: chunks.append(f"[KEYWORD]: {s}")
                if chunks:
                    reranked = await rerank_chunks(q, chunks, top_k=8)
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
                    tool_result_str = f"[GDS ERROR]: {e}"
            else:
                tool_result_str = f"Tool {func_name} executed."

            single_tool_ms = (time.perf_counter() - t_single_tool) * 1000
            loop_info["tool_calls"].append({
                "name": func_name,
                "args": args,
                "dur_ms": single_tool_ms,
                "result_chars": len(tool_result_str),
                "result_tokens": count_tokens(tool_result_str)
            })
            print(f"    └─ Gọi Tool: `{func_name}` | Thời gian: {single_tool_ms:.1f}ms | Kết quả: {count_tokens(tool_result_str)} tokens")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": func_name,
                "content": tool_result_str
            })

        loop_info["tool_execution_ms"] = (time.perf_counter() - t_tools_start) * 1000
        loop_info["loop_total_ms"] = (time.perf_counter() - t_loop_start) * 1000
        loop_traces.append(loop_info)
        timings[f"03_pass1_loop_{loop_count}_total"] = loop_info["loop_total_ms"]

    # 4. Context Assembly & GDS Auto-Synthesis
    t0 = time.perf_counter()
    tool_context = []
    for m in messages:
        if m["role"] == "tool":
            tool_context.append(f"<{m.get('name', 'tool')}_data>\n{m.get('content', '')}\n</{m.get('name', 'tool')}_data>")

    has_gds = any("gds" in m.lower() for m in tool_context)
    if not has_gds:
        try:
            from core.gds_service import GDSService
            candidates = ["TS. Hùng", "Đồ án STM32", "Board STM32 bị nổ", "Nam", "Game Valorant", "STM32"]
            matched_ents = [c for c in candidates if c.lower() in COMPLEX_1K_PROMPT.lower()]
            gds_context = await GDSService.synthesize_gds_context(int(user_id), entities=matched_ents or None)
            if gds_context:
                tool_context.append(f"<gds_causal_topology>\n{gds_context}\n</gds_causal_topology>")
        except Exception as exc:
            pass

    context_str = "\n".join(tool_context) if tool_context else "<system_state>No additional DB events.</system_state>"
    tokens["sensor_truth_context"] = count_tokens(context_str)

    raphael_prompt = f"""
<sensor_truth>
{context_str}
</sensor_truth>
<chat_history>
{COMPLEX_1K_PROMPT}
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
    timings["04_context_assembly_and_gds"] = (time.perf_counter() - t0) * 1000

    tokens["system_raphael"] = count_tokens(SYSTEM_RAPHAEL)
    tokens["pass2_raphael_prompt"] = count_tokens(raphael_prompt)
    tokens["pass2_total_input"] = tokens["system_raphael"] + tokens["pass2_raphael_prompt"]

    # 5. Pass 2 Persona Synthesis (Deep Thinking ENABLED)
    print("\n[PHASE 2] Khởi chạy Pass 2 Cognitive Synthesis (Thinking ENABLED)...")
    t0 = time.perf_counter()
    try:
        if settings.deepseek_reasoning_effort.lower() in ("none", "disabled", "off"):
            pass2_extra = {"thinking": {"type": "disabled"}}
        else:
            pass2_extra = {"reasoning_effort": settings.deepseek_reasoning_effort}

        response2 = await client.chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": SYSTEM_RAPHAEL},
                {"role": "user", "content": raphael_prompt}
            ],
            max_tokens=settings.deepseek_max_tokens,
            temperature=0.0,
            extra_body=pass2_extra
        )
        timings["05_pass2_deepseek_synthesis"] = (time.perf_counter() - t0) * 1000
    except Exception as e:
        timings["05_pass2_deepseek_synthesis"] = (time.perf_counter() - t0) * 1000
        print(f"  ❌ Pass 2 LLM Error: {e}")
        return

    msg2 = response2.choices[0].message
    final_text = msg2.content or ""
    reasoning_text = getattr(msg2, "reasoning_content", None) or ""

    thinking_match = re.search(r'<thinking>(.*?)</thinking>', final_text, flags=re.DOTALL)
    if thinking_match:
        if not reasoning_text:
            reasoning_text = thinking_match.group(1).strip()
        final_text = re.sub(r'<thinking>.*?</thinking>', '', final_text, flags=re.DOTALL).strip()

    tokens["pass2_reasoning_tokens"] = count_tokens(reasoning_text)
    tokens["pass2_spoken_tokens"] = count_tokens(final_text)
    tokens["pass2_total_output"] = tokens["pass2_reasoning_tokens"] + tokens["pass2_spoken_tokens"]

    if hasattr(response2, "usage") and response2.usage:
        tokens["pass2_api_prompt_tokens"] = getattr(response2.usage, "prompt_tokens", 0)
        tokens["pass2_api_completion_tokens"] = getattr(response2.usage, "completion_tokens", 0)

    # 6. Post-processing & HUD
    t0 = time.perf_counter()
    hud_line, _ = await build_hud(int(user_id))
    timings["06_hud_and_postprocessing"] = (time.perf_counter() - t0) * 1000

    total_latency_ms = (time.perf_counter() - t_global_start) * 1000
    timings["total_end_to_end"] = total_latency_ms

    # 7. Print Comprehensive Engineering Report
    print("\n" + "=" * 90)
    print("📋 BÁO CÁO PHÂN TÍCH KỸ THUẬT CHI TIẾT (ENGINEERING WATERFALL & INVENTORY)")
    print("=" * 90)

    print("\n1. THỐNG KÊ CHI TIẾT ĐỘ TRỄ THEO TỪNG CÔNG ĐOẠN (LATENCY WATERFALL):")
    print(f"   ┌──────────────────────────────────────────────┬────────────┬─────────────┐")
    print(f"   │ Công đoạn xử lý (Pipeline Stage)             │ Độ trễ(ms) │ Tỷ trọng(%) │")
    print(f"   ├──────────────────────────────────────────────┼────────────┼─────────────┤")
    for k, v in timings.items():
        if k == "total_end_to_end": continue
        pct = (v / total_latency_ms) * 100.0
        stage_name = k.replace("_", " ").title()
        print(f"   │ {stage_name:<44} │ {v:>8.1f}ms │ {pct:>9.2f}% │")
    print(f"   ├──────────────────────────────────────────────┼────────────┼─────────────┤")
    print(f"   │ TỔNG THỜI GIAN TOÀN TRÌNH (END-TO-END)       │ {total_latency_ms:>8.1f}ms │     100.00% │ ({total_latency_ms/1000.0:.2f}s)")
    print(f"   └──────────────────────────────────────────────┴────────────┴─────────────┘")

    print("\n2. CHI TIẾT CÁC LẦN LẶP (AGENTIC LOOP TRACE):")
    for tr in loop_traces:
        print(f"   • Vòng lặp #{tr['loop_index']}:")
        print(f"     - Thời gian LLM ra quyết định: {tr['llm_ms']:.1f}ms")
        print(f"     - Số công cụ được gọi: {len(tr['tool_calls'])}")
        for tc in tr["tool_calls"]:
            print(f"       + Công cụ: `{tc['name']}` | Thời gian chạy: {tc['dur_ms']:.1f}ms | Output: {tc['result_tokens']} tokens")
        print(f"     - Tổng thời gian thực thi công cụ: {tr['tool_execution_ms']:.1f}ms")
        print(f"     - Tổng thời gian vòng lặp: {tr['loop_total_ms']:.1f}ms")

    print("\n3. BẢNG KIỂM KÊ TOKENS CHÍNH XÁC (EXACT TOKEN INVENTORY):")
    print(f"   ┌────────────────────────────────────────────────────────┬─────────────┐")
    print(f"   │ Thành phần Ngữ cảnh & Hệ thống                         │ Số Tokens   │")
    print(f"   ├────────────────────────────────────────────────────────┼─────────────┤")
    print(f"   │ [A] SYSTEM PROMPTS:                                    │             │")
    print(f"   │     • System Prompt Pass 1 (SYSTEM_ORCHESTRATOR)       │ {tokens.get('system_orchestrator', 0):>9,d} t │")
    print(f"   │     • System Prompt Pass 2 (SYSTEM_RAPHAEL)            │ {tokens.get('system_raphael', 0):>9,d} t │")
    print(f"   │                                                        │             │")
    print(f"   │ [B] NGỮ CẢNH DỮ LIỆU & ĐẦU VÀO:                        │             │")
    print(f"   │     • User Message Gốc (COMPLEX_1K_PROMPT)             │ {tokens.get('user_prompt', 0):>9,d} t │")
    print(f"   │     • Mini-Context SQLite (Trạng thái, chỉ số gần nhất)│ {tokens.get('mini_ctx', 0):>9,d} t │")
    print(f"   │     • Ngữ cảnh <sensor_truth> (GDS + Tri-Store tools)  │ {tokens.get('sensor_truth_context', 0):>9,d} t │")
    print(f"   │                                                        │             │")
    print(f"   │ [C] TỔNG ĐẦU VÀO (INPUT TOKENS BẬC 2):                 │             │")
    print(f"   │     • Tổng Prompt gửi tới Pass 2 (Raphael Prompt)      │ {tokens.get('pass2_raphael_prompt', 0):>9,d} t │")
    print(f"   │     • TỔNG INPUT TOKENS PASS 2 (System + Prompt)       │ {tokens.get('pass2_total_input', 0):>9,d} t │")
    print(f"   │                                                        │             │")
    print(f"   │ [D] ĐẦU RA (OUTPUT TOKENS):                            │             │")
    print(f"   │     • Reasoning Tokens (<thinking> - Suy luận ẩn)      │ {tokens.get('pass2_reasoning_tokens', 0):>9,d} t │")
    print(f"   │     • Spoken Voice Tokens (Giọng nói phát ra)          │ {tokens.get('pass2_spoken_tokens', 0):>9,d} t │")
    print(f"   │     • TỔNG OUTPUT TOKENS BỊ TÍNH TIỀN                  │ {tokens.get('pass2_total_output', 0):>9,d} t │")
    print(f"   └────────────────────────────────────────────────────────┴─────────────┘")

    print("\n4. NỘI DUNG PHẢN HỒI THỰC TẾ:")
    print(f"   • Giọng nói: {final_text}")
    print(f"   • Thinking:\n{reasoning_text}\n")

if __name__ == "__main__":
    asyncio.run(profile_deep_dive())
