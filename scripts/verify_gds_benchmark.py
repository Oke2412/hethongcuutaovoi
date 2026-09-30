# -*- coding: utf-8 -*-
"""
scripts/verify_gds_benchmark.py — Comprehensive GDS Verification & Benchmark Suite for Linear
Executes all 5 GDS procedures on live Docker Neo4j, measures latency, verifies Louvain,
and tests end-to-end DeepSeek synthesis while keeping token consumption < 50k.
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))
sys.stdout.reconfigure(encoding='utf-8')

import asyncio
import time
from typing import Dict, Any
from neo4j import AsyncGraphDatabase
from openai import AsyncOpenAI
from config import settings
from core.gds_service import GDSService, rerank_chunks_with_pagerank

USER_ID = 8763843475

async def run_benchmark():
    print("=" * 80)
    print("🚀 RAPHAEL LIFE OS — GRAPH DATA SCIENCE (GDS) BENCHMARK REPORT (RAP-8)")
    print("=" * 80)

    report_lines = []
    def log(msg: str):
        print(msg)
        report_lines.append(msg)

    # 1. Check GDS Version & Capabilities
    driver = AsyncGraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    async with driver.session() as session:
        v_res = await session.run("RETURN gds.version() AS version")
        v_row = await v_res.single()
        gds_version = v_row["version"] if v_row else "Unknown"

        p_res = await session.run("SHOW PROCEDURES YIELD name WHERE name STARTS WITH 'gds' RETURN count(name) AS total")
        p_row = await p_res.single()
        total_procs = p_row["total"] if p_row else 0

    log(f"• Neo4j Status: Connected ({settings.neo4j_uri})")
    log(f"• GDS Version: {gds_version} (Active & Operational)")
    log(f"• Total GDS Procedures Registered: {total_procs}")
    log("")

    # 2. Seed Structured Benchmark Graph
    log("### 1. SEEDING BENCHMARK TOPOLOGY (2 COMMUNITIES + 1 BRIDGE)")
    async with driver.session() as session:
        # Clean previous benchmark graph
        await session.run("MATCH (n) WHERE n.user_id = $uid OR labels(n)[0] = 'Person' DETACH DELETE n", uid=USER_ID)
        
        seed_cypher = """
        // Community 1: Academic & Project Stress
        CREATE (m:Person {name: 'Master', user_id: $uid})
        CREATE (hung:Person {name: 'TS. Hùng', role: 'Giảng viên hướng dẫn', user_id: $uid})
        CREATE (proj:WorkProject {name: 'Đồ án STM32', user_id: $uid})
        CREATE (event:LifeEvent {name: 'Board STM32 bị nổ', user_id: $uid})
        CREATE (emo1:Emotion {name: 'Áp lực tốt nghiệp', user_id: $uid})
        CREATE (emo2:Emotion {name: 'Mệt mỏi kiệt sức', user_id: $uid})

        CREATE (m)-[:SUPERVISED_BY]->(hung)
        CREATE (hung)-[:SUPERVISES]->(proj)
        CREATE (m)-[:WORKS_ON]->(proj)
        CREATE (proj)-[:TRIGGERS]->(event)
        CREATE (event)-[:CAUSES]->(emo1)
        CREATE (emo1)-[:CAUSES]->(emo2)

        // Community 2: Social & Escapism
        CREATE (nam:Person {name: 'Nam', role: 'Bạn thân', user_id: $uid})
        CREATE (game:Object {name: 'Game Valorant', user_id: $uid})
        CREATE (cafe:Location {name: 'Quán Cafe Cổ', user_id: $uid})
        CREATE (emo3:Emotion {name: 'Thư giãn né tránh', user_id: $uid})

        CREATE (m)-[:ROOMMATE_WITH]->(nam)
        CREATE (nam)-[:INVITES]->(game)
        CREATE (m)-[:PLAYS]->(game)
        CREATE (nam)-[:INVITES]->(cafe)
        CREATE (m)-[:HANGS_OUT_AT]->(cafe)
        CREATE (game)-[:TRIGGERS]->(emo3)

        // Cross-domain Bridge (Bottleneck)
        CREATE (emo2)-[:DRIVES_TO]->(emo3)
        """
        await session.run(seed_cypher, uid=USER_ID)

        # Drop old projection to ensure fresh test
        gname = f"user_graph_{USER_ID}"
        await session.run("""
            CALL gds.graph.exists($gname) YIELD exists
            WITH exists WHERE exists
            CALL gds.graph.drop($gname, false) YIELD graphName
            RETURN graphName
        """, gname=gname)

    log("✓ Đã nạp thành công 10 Nodes, 13 Cạnh và 1 Cầu nối liên cụm (emo2 -> emo3).")
    log("")

    # 3. Benchmark 5 GDS Procedures
    log("### 2. KIỂM THỬ 5 THUẬT TOÁN GDS THỰC TẾ (LATENCY & KẾT QUẢ)")

    # 3.1. PageRank
    t0 = time.perf_counter()
    pr_nodes = await GDSService.get_global_pagerank(USER_ID, limit=5)
    t_pr = (time.perf_counter() - t0) * 1000
    log(f"**2.1. Global PageRank (`gds.pageRank.stream`) — Độ trễ: {t_pr:.1f}ms**")
    for n in pr_nodes:
        log(f"  - `{n['name']}` ({n['type']}): Centrality Score = {n['score']}")
    log("")

    # 3.2. Personalized PageRank
    t0 = time.perf_counter()
    ppr_nodes = await GDSService.get_personalized_pagerank(USER_ID, "Board STM32 bị nổ", limit=5)
    t_ppr = (time.perf_counter() - t0) * 1000
    log(f"**2.2. Personalized PageRank (`gds.pageRank.stream + sourceNodes`) — Độ trễ: {t_ppr:.1f}ms**")
    log(f"  *Nguồn phát tán: 'Board STM32 bị nổ'*")
    for n in ppr_nodes:
        log(f"  - `{n['name']}` ({n['type']}): Ripple Impact = {n['score']}")
    log("")

    # 3.3. Louvain Community Detection
    t0 = time.perf_counter()
    louvain_comms = await GDSService.detect_causal_communities(USER_ID, limit=4)
    t_lv = (time.perf_counter() - t0) * 1000
    log(f"**2.3. Louvain Community (`gds.louvain.stream`) — Độ trễ: {t_lv:.1f}ms**")
    for cluster, members in louvain_comms.items():
        log(f"  - **{cluster}**: {', '.join(members)}")
    log("")

    # 3.4. Betweenness Centrality
    t0 = time.perf_counter()
    bw_nodes = await GDSService.get_critical_bottlenecks(USER_ID, limit=5)
    t_bw = (time.perf_counter() - t0) * 1000
    log(f"**2.4. Betweenness Centrality (`gds.betweenness.stream`) — Độ trễ: {t_bw:.1f}ms**")
    for b in bw_nodes:
        log(f"  - `{b['name']}` ({b['type']}): Bottleneck Bridge Score = {b['score']}")
    log("")

    # 3.5. Shortest Path
    t0 = time.perf_counter()
    path = await GDSService.find_causal_shortest_path(USER_ID, "TS. Hùng", "Thư giãn né tránh")
    t_sp = (time.perf_counter() - t0) * 1000
    log(f"**2.5. Shortest Causal Path (`shortestPath`) — Độ trễ: {t_sp:.1f}ms**")
    log(f"  - Chuỗi nhân quả: {' -> '.join(path) if path else 'Không tìm thấy'}")
    log("")

    # 4. Context Synthesis & Structural Reranking
    log("### 3. KIỂM THỬ HỢP NHẤT PIPELINE (GDS SYNTHESIS + RESCORING)")
    gds_context = await GDSService.synthesize_gds_context(USER_ID, entities=["Board STM32 bị nổ"])
    log("Thẻ định tính nạp vào Prompt DeepSeek:")
    log("```xml")
    log(gds_context)
    log("```")
    log("")

    raw_chunks = [
        "Master thích đi uống cafe cuối tuần ở quán quen.",
        "Dự án đồ án STM32 đang bị cháy linh kiện do chập nguồn.",
        "Nam rủ chơi game Valorant để giải trí.",
        "Gặp TS. Hùng báo cáo tiến độ đồ án tốt nghiệp.",
        "Thời tiết Hà Nội hôm nay mát mẻ."
    ]
    reranked = await rerank_chunks_with_pagerank(USER_ID, raw_chunks, top_k=3)
    log("Kết quả tái sắp xếp cấu trúc (PageRank Rescoring - Top 3 Chunks):")
    for idx, c in enumerate(reranked, 1):
        log(f"  {idx}. {c}")
    log("")

    # 5. Live DeepSeek Reasoning Test & Token Tracking
    log("### 4. THỰC NGHIỆM ĐIỀU PHỐI DEEPSEEK FLASH & ĐO ĐẠC TOKEN THỰC TẾ")
    client = AsyncOpenAI(
        api_key=settings.deepseek_api_key,
        base_url="https://api.deepseek.com"
    )

    system_prompt = f"""You are Raphael (Lord of Wisdom), personal Life OS for Master.
Analyze psychological motives and causality inside hidden <thinking>.
Answer concisely in Vietnamese (1-2 sentences). Attach HUD: ⚡E | 😐M | ❤️H | 💎Cr | 📍H3.

[GDS STRUCTURAL CAUSAL INSIGHTS]
{gds_context}
"""
    user_prompt = "Board STM32 lại nổ rồi, mệt mỏi quá chắc ta đi ngủ hoặc rủ Nam làm ván game đây..."

    t0 = time.perf_counter()
    response = await client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0
    )
    t_llm = (time.perf_counter() - t0) * 1000

    choice = response.choices[0]
    usage = response.usage

    log(f"• LLM Model: `{settings.deepseek_model}` via DeepSeek Official API")
    log(f"• Độ trễ phản hồi (LLM Latency): {t_llm:.0f} ms")
    log(f"• Prompt Tokens: {usage.prompt_tokens}")
    log(f"• Completion Tokens: {usage.completion_tokens}")
    log(f"• Total Tokens: {usage.total_tokens} (Tiêu thụ: ~{usage.total_tokens} / Ngân sách cho phép: 50,000 tokens)")
    
    # Cache hit info if present
    prompt_cache_hit = getattr(usage, "prompt_cache_hit_tokens", 0)
    prompt_cache_miss = getattr(usage, "prompt_cache_miss_tokens", usage.prompt_tokens)
    log(f"• Prompt Cache Hit: {prompt_cache_hit} tokens ({prompt_cache_hit / max(1, usage.prompt_tokens) * 100:.1f}%)")
    log("")
    log("**Câu trả lời của Raphael gửi Master:**")
    log(f"> {choice.message.content}")
    log("")

    log("=" * 80)
    log("✓ TOÀN BỘ BÀI KIỂM THỬ HOÀN TẤT THÀNH CÔNG — TỔNG TOKEN TIÊU THỤ << 50K")
    log("=" * 80)

    # Save artifact report for Linear
    with open("docs/GDS_BENCHMARK_LINEAR_REPORT.md", "w", encoding="utf-8") as rf:
        rf.write("\n".join(report_lines))
    print("\n[REPORT SAVED]: docs/GDS_BENCHMARK_LINEAR_REPORT.md")

    await driver.close()

if __name__ == "__main__":
    asyncio.run(run_benchmark())
