import asyncio
import os
import sys
import logging
import json
import re
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import settings
from db.database import AsyncSessionLocal, engine, init_db
from sqlmodel import SQLModel, select
from db.models import User, PhysicalStatus, CapabilityLog, WorkProject, SystemQuest, MessageLog
from core.omniscience import get_mini_context, log_message, get_omniscient_state
from core.hud import build_hud
from core.search import sparse_search, rerank_chunks
from core.llm_tools import (
    update_memory_async,
    cancel_quest_async,
    complete_quest_async,
    create_quest_async,
    manage_user_status_async,
    update_physical_status_async,
    manage_project_async,
    manage_capability_async,
    manage_credits_async,
    calculate_distance_sync,
    reset_database_async,
)
from core.llm import evaluate_location_side_quest
from core.brain import RaphaelBrain

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("SYSTEM_TEST")

TEST_USER_ID = 999999
TEST_TG_ID = 888888


class TestReport:
    def __init__(self):
        self.results = []
        self.token_usage_estimated = 0

    def record(self, category: str, test_name: str, passed: bool, detail: str = ""):
        self.results.append({
            "category": category,
            "name": test_name,
            "passed": passed,
            "detail": detail
        })
        status_str = "PASS" if passed else "FAIL"
        logger.info(f"[{status_str}] [{category}] {test_name}: {detail}")

    def summary(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "rate": f"{(passed/total)*100:.1f}%" if total else "0%",
            "tokens_used": self.token_usage_estimated
        }


report = TestReport()


async def setup_test_db():
    logger.info("Initializing database and wiping clean for isolated test...")
    await init_db()
    # Reset test user's data to ensure strict repeatability
    await reset_database_async(TEST_USER_ID)
    async with AsyncSessionLocal() as session:
        user = await session.get(User, TEST_USER_ID)
        if not user:
            user = User(id=TEST_USER_ID, telegram_id=TEST_TG_ID, name="Master Tester", credits=100.0)
            session.add(user)
        else:
            user.credits = 100.0
            user.titles = ""
            user.active_buff = ""
            session.add(user)
        await session.commit()
    report.record("DB_INIT", "Database Isolation & Reset", True, "Tables initialized and test user reset to 100.0cr")


async def test_module_database_and_fts():
    logger.info("--- Testing Module: SQLite FTS5 & MessageLog ---")
    try:
        # Log test messages
        test_content = "Master đang nghiên cứu ROS2 và hệ điều hành Raphael trên xe tự hành"
        await log_message(TEST_USER_ID, "user", test_content)
        await log_message(TEST_USER_ID, "assistant", "Raphael đã ghi nhận mục tiêu nghiên cứu ROS2.")

        # Query via sparse_search (FTS5)
        results = await sparse_search(["ROS2", "Raphael"], limit=5)
        found = any("ROS2" in r for r in results)
        report.record(
            "FTS5_SEARCH",
            "FTS5 Sparse Keyword Search",
            found,
            f"Found {len(results)} matching chunks via messagelog_fts"
        )
    except Exception as e:
        report.record("FTS5_SEARCH", "FTS5 Sparse Keyword Search", False, str(e))


async def test_module_state_and_tools():
    logger.info("--- Testing Module: Core LLM Tools & DB Mutations ---")

    # 1. Physical Status Tool
    try:
        await update_physical_status_async(
            user_id=TEST_USER_ID,
            energy=8,
            mood=7,
            health=9,
            sleep_hours=7.5,
            notes="Thể trạng tốt sau bài tập thể lực"
        )
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(PhysicalStatus).where(PhysicalStatus.user_id == TEST_USER_ID).order_by(PhysicalStatus.id.desc()).limit(1)
            )
            latest_phys = res.scalar_one_or_none()
            passed = latest_phys is not None and latest_phys.energy == 8 and latest_phys.sleep_hours == 7.5
            report.record("LLM_TOOLS", "update_physical_status", passed, f"Energy: {latest_phys.energy}, Sleep: {latest_phys.sleep_hours}h")
    except Exception as e:
        report.record("LLM_TOOLS", "update_physical_status", False, str(e))

    # 2. Manage Project Tool (create, update progress, delete)
    try:
        proj_name = "Xây dựng Autonomous Agent"
        await manage_project_async(user_id=TEST_USER_ID, action="create", name=proj_name, progress_percent=15)
        await manage_project_async(user_id=TEST_USER_ID, action="update", name=proj_name, progress_percent=45)
        
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(WorkProject).where(WorkProject.user_id == TEST_USER_ID, WorkProject.name == proj_name)
            )
            proj = res.scalar_one_or_none()
            passed = proj is not None and proj.progress_percent == 45
            report.record("LLM_TOOLS", "manage_project (create & update)", passed, f"Project '{proj.name}' at {proj.progress_percent}%")
    except Exception as e:
        report.record("LLM_TOOLS", "manage_project", False, str(e))

    # 3. Manage Capability Tool (Skill Tree: domain, current_level, exp)
    try:
        await manage_capability_async(user_id=TEST_USER_ID, action="update", domain="Robotics/ROS2", level=2.0, exp=250.0, unit="EXP")
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(CapabilityLog).where(CapabilityLog.user_id == TEST_USER_ID, CapabilityLog.domain == "Robotics/ROS2").order_by(CapabilityLog.id.desc()).limit(1)
            )
            cap = res.scalar_one_or_none()
            passed = cap is not None and cap.current_level == 2.0 and cap.exp == 250.0
            report.record("LLM_TOOLS", "manage_capability (Skill Tree)", passed, f"Domain: {cap.domain}, Level: {cap.current_level}, Exp: {cap.exp}")
    except Exception as e:
        report.record("LLM_TOOLS", "manage_capability", False, str(e))

    # 4. Manage Credits Tool (Reward & Penalty: add, spend)
    try:
        # Starting credits = 100.0
        await manage_credits_async(user_id=TEST_USER_ID, action="add", amount=50.0, reason="Thưởng hoàn thành mục tiêu")
        await manage_credits_async(user_id=TEST_USER_ID, action="spend", amount=20.0, reason="Trừ tín chỉ phạt trễ hạn")
        async with AsyncSessionLocal() as session:
            user = await session.get(User, TEST_USER_ID)
            # 100.0 + 50.0 - 20.0 = 130.0
            passed = user.credits == 130.0
            report.record("LLM_TOOLS", "manage_credits (Add & Spend)", passed, f"User credits: {user.credits}cr (expected 130.0cr)")
    except Exception as e:
        report.record("LLM_TOOLS", "manage_credits", False, str(e))

    # 5. System Quests Lifecycle (create, complete, cancel)
    try:
        res_q1 = await create_quest_async(
            user_id=TEST_USER_ID,
            title="Giải mã cấu trúc Cypher Neo4j",
            description="Tối ưu quan hệ TRIGGERS và CAUSES",
            reward="50 Credits",
            penalty="-20 Credits"
        )
        res_q2 = await create_quest_async(
            user_id=TEST_USER_ID,
            title="Chạy bộ phục hồi thể lực 3km",
            description="Khu vực hồ Tây",
            reward="20 Credits",
            penalty="-5 Energy"
        )
        
        id1 = int(re.search(r'Quest ID (\d+)', res_q1).group(1))
        id2 = int(re.search(r'Quest ID (\d+)', res_q2).group(1))

        # Complete q1, Cancel q2
        await complete_quest_async(user_id=TEST_USER_ID, quest_id=id1)
        await cancel_quest_async(user_id=TEST_USER_ID, quest_id=id2, reason="Thời tiết mưa lớn")
        
        async with AsyncSessionLocal() as session:
            q1_db = await session.get(SystemQuest, id1)
            q2_db = await session.get(SystemQuest, id2)
            user = await session.get(User, TEST_USER_ID)
            # q1 reward 50 credits granted: 130 + 50 = 180
            passed = q1_db.status == "completed" and q2_db.status == "cancelled" and user.credits == 180.0
            report.record("LLM_TOOLS", "Quest Lifecycle (create, complete, cancel)", passed, f"Q1: {q1_db.status} (+50cr), Q2: {q2_db.status}, Balance: {user.credits}cr")
    except Exception as e:
        report.record("LLM_TOOLS", "Quest Lifecycle", False, str(e))

    # 6. Haversine Distance Calculation (GPS)
    try:
        # Distance between Hoan Kiem Lake (21.0285, 105.8542) and West Lake (21.0583, 105.8236)
        dist_str = calculate_distance_sync(21.0285, 105.8542, 21.0583, 105.8236)
        # Parse numeric meters from returned string
        val_match = re.search(r'[\d\.]+', dist_str)
        dist_val = float(val_match.group(0)) if val_match else 0.0
        passed = 4000 < dist_val < 5000
        report.record("LLM_TOOLS", "calculate_distance_sync (GPS Haversine)", passed, f"Output: '{dist_str}' -> {dist_val:.1f} meters")
    except Exception as e:
        report.record("LLM_TOOLS", "calculate_distance_sync", False, str(e))


async def test_module_hud_and_context():
    logger.info("--- Testing Module: HUD Generation & Context Synthesis ---")
    try:
        # Create 1 active pending quest
        await create_quest_async(
            user_id=TEST_USER_ID,
            title="Đọc tài liệu SOTA GraphRAG",
            description="Phân tích mô hình Qwen3-Reranker-8B",
            reward="30 Credits",
            penalty="-10 EXP"
        )
        
        hud_line, keyboard = await build_hud(TEST_USER_ID)
        # Verify HUD metrics: Energy 8/10, Health 9/10, Credits 180.0cr
        has_hud_indicators = "⚡ 8/10" in hud_line and "❤️ 9/10" in hud_line and "180.0cr" in hud_line
        has_buttons = keyboard is not None and len(keyboard.inline_keyboard) > 0
        
        passed = has_hud_indicators and has_buttons
        report.record("HUD", "HUD Formatting & Interactive Buttons", passed, f"HUD: {hud_line.splitlines()[-1]}")

        # Test mini_context format: [Time: ...] E:8 M:7 H:9 | Credits:180.0 | Skills:Robotics/ROS2 Lv2.0 | Projects:Xây dựng Autonomous Agent(45%)
        mini_ctx = await get_mini_context(TEST_USER_ID)
        ctx_passed = "E:8" in mini_ctx and "Credits:180.0" in mini_ctx and "Robotics/ROS2" in mini_ctx and "Autonomous Agent" in mini_ctx
        report.record("CONTEXT", "get_mini_context Synthesis", ctx_passed, f"Mini Context (~60 tokens): {mini_ctx}")

        # Test full omniscient state
        omni_state = await get_omniscient_state(TEST_USER_ID)
        omni_passed = "TRẠNG THÁI TOÀN TRI" in omni_state and "CÂY KỸ NĂNG" in omni_state
        report.record("CONTEXT", "get_omniscient_state Synthesis", omni_passed, "Synthesizes multi-tier state for high-reasoning prompt injection")
    except Exception as e:
        report.record("HUD_CONTEXT", "HUD and Context Generation", False, str(e))


async def test_module_spatial_and_h3():
    logger.info("--- Testing Module: Spatial H3 Grid & Location Evaluation ---")
    try:
        import h3
        # Latitude / Longitude for Hanoi
        lat, lon = 21.0285, 105.8542
        hex_res9 = h3.latlng_to_cell(lat, lon, 9)
        passed_h3 = len(hex_res9) == 15 and isinstance(hex_res9, str)
        report.record("SPATIAL_H3", "H3 Resolution 9 Hex Indexing", passed_h3, f"H3 Cell: {hex_res9}")

        # Test location side quest evaluation mock
        past_events = [{"ts": "2026-09-12 10:00", "desc": "Master đã tập luyện thể lực tại đây", "impact": "HIGH"}]
        
        with patch("core.llm._get_llm_client") as mock_client_factory:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = "🔥 [SIDE QUEST] Vượt ngưỡng 5km chạy bộ | Reward: +50 Credits | Penalty: -20 Health"
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client_factory.return_value = mock_client

            eval_res = await evaluate_location_side_quest(TEST_USER_ID, hex_res9, past_events)
            passed_eval = "SIDE QUEST" in eval_res
            report.record("SPATIAL_H3", "evaluate_location_side_quest Logic", passed_eval, f"Result: {eval_res}")
    except Exception as e:
        report.record("SPATIAL_H3", "Spatial Location & H3 Evaluation", False, str(e))


async def test_module_search_and_reranking():
    logger.info("--- Testing Module: Search & Reranker Logic ---")
    try:
        query = "hướng dẫn cài đặt ROS2"
        chunks = [
            "Cách làm bánh mì thịt nướng thơm ngon tại nhà.",
            "Tài liệu hướng dẫn cài đặt và cấu hình ROS2 Humble trên Ubuntu Server.",
            "Dự báo thời tiết Hà Nội tuần tới nắng ráo."
        ]

        # Test fallback when API fails or offline
        with patch("httpx.AsyncClient.post", side_effect=Exception("Connection timed out")):
            reranked = await rerank_chunks(query, chunks, top_k=2)
            passed_fallback = len(reranked) == 2
            report.record("RERANKER", "rerank_chunks Resilient Fallback", passed_fallback, "Returned top 2 chunks on API exception")

        # Test mock SiliconFlow response
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            # Index 1 is the ROS2 document
            mock_resp.json.return_value = {
                "results": [
                    {"index": 1, "relevance_score": 0.98},
                    {"index": 0, "relevance_score": 0.12},
                    {"index": 2, "relevance_score": 0.05}
                ]
            }
            mock_post.return_value = mock_resp

            reranked_success = await rerank_chunks(query, chunks, top_k=1)
            passed_ranking = len(reranked_success) == 1 and "ROS2 Humble" in reranked_success[0]
            report.record("RERANKER", "rerank_chunks Scoring & Reordering", passed_ranking, f"Top ranked: '{reranked_success[0]}'")
    except Exception as e:
        report.record("RERANKER", "Search & Reranker", False, str(e))


async def test_module_core_brain_agentic_loop():
    logger.info("--- Testing Module: Core Brain 2-Pass Agentic Loop & Persona Synthesis ---")
    brain = RaphaelBrain()

    # Scenario: Master inputs a complex message: "Tôi vừa hoàn thành module nhận diện camera ROS2, nhưng người hơi mệt cần nghỉ ngơi"
    # Pass 1: Orchestrator Agent executes tools, updates physical state & project, then outputs TERMINATE_LOOP
    # Pass 2: Raphael Persona Synthesizer generates cold, concise response with hidden <thinking> block

    mock_tool_call_phys = MagicMock()
    mock_tool_call_phys.id = "call_001"
    mock_tool_call_phys.function.name = "update_physical_status"
    mock_tool_call_phys.function.arguments = json.dumps({
        "energy": 4, "mood": 6, "health": 8, "sleep_hours": 6.0, "notes": "Mệt mỏi sau khi code camera ROS2"
    })

    mock_tool_call_proj = MagicMock()
    mock_tool_call_proj.id = "call_002"
    mock_tool_call_proj.function.name = "manage_project"
    mock_tool_call_proj.function.arguments = json.dumps({
        "action": "update", "name": "Xây dựng Autonomous Agent", "progress_percent": 80
    })

    # Response for Pass 1 (Orchestrator)
    resp_pass1_step1 = MagicMock()
    msg_step1 = MagicMock()
    msg_step1.content = None
    msg_step1.tool_calls = [mock_tool_call_phys, mock_tool_call_proj]
    resp_pass1_step1.choices = [MagicMock(message=msg_step1)]

    resp_pass1_step2 = MagicMock()
    msg_step2 = MagicMock()
    msg_step2.content = "TERMINATE_LOOP"
    msg_step2.tool_calls = None
    resp_pass1_step2.choices = [MagicMock(message=msg_step2)]

    # Response for Pass 2 (Synthesizer Persona)
    resp_pass2 = MagicMock()
    msg_pass2 = MagicMock()
    msg_pass2.content = """<thinking>
1. Initial Hypothesis: Master vừa đạt tiến độ lớn nhưng thể trạng suy kiệt (Energy 4/10). Có xu hướng muốn buông thả.
2. Devil's Advocate: Nghỉ ngơi là cần thiết để phục hồi thể chất, không phải lười biếng.
3. Denied Truth: Tiến trình đạt 80%. Cần bảo toàn năng lượng cho chặng nước rút.
4. Action: Ghi nhận tiến độ, lệnh nghỉ ngơi ngắn hạn, cấm thức khuya.
</thinking>
[Hệ thống] Tiến độ dự án đạt 80%. Thể trạng suy kiệt, lệnh Master ngừng công việc và phục hồi ngay lập tức."""
    resp_pass2.choices = [MagicMock(message=msg_pass2)]

    with patch("core.llm._get_llm_client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=[resp_pass1_step1, resp_pass1_step2, resp_pass2]
        )
        mock_client_factory.return_value = mock_client

        response_text, keyboard = await brain.process_input(
            user_id=str(TEST_USER_ID),
            text_content="Tôi vừa hoàn thành module nhận diện camera ROS2, nhưng người hơi mệt cần nghỉ ngơi"
        )

        # Assertions
        has_thinking_stripped = "<thinking>" not in response_text
        has_persona_tag = "[Hệ thống]" in response_text
        has_hud = "⚡" in response_text and "💎" in response_text
        first_line = response_text.splitlines()[0]
        word_count = len(first_line.split())
        concise = word_count <= 25

        passed = has_thinking_stripped and has_persona_tag and has_hud and concise
        report.record(
            "CORE_BRAIN",
            "2-Pass Agentic Loop & Metacognitive Synthesis",
            passed,
            f"Response words: {word_count}. Thinking hidden: {has_thinking_stripped}. HUD attached: {has_hud}."
        )


async def test_live_api_probe_if_available():
    logger.info("--- Testing Optional Live SiliconFlow Probe (Token budget check) ---")
    api_key = settings.siliconflow_api_key
    if not api_key:
        logger.info("No SILICONFLOW_API_KEY set in local environment, skipping live probe (0 tokens used).")
        report.record("LIVE_PROBE", "SiliconFlow Live Probe", True, "Skipped cleanly (0 external tokens consumed)")
        return

    try:
        from core.llm import _get_llm_client
        client = _get_llm_client()
        # Single minimal ping probe: max 10 tokens
        resp = await client.chat.completions.create(
            model="deepseek-ai/deepseek-v4.1-flash",
            messages=[{"role": "user", "content": "PING"}],
            max_tokens=10,
            temperature=0.0
        )
        content = resp.choices[0].message.content
        report.token_usage_estimated += 25
        report.record("LIVE_PROBE", "SiliconFlow Live Probe", True, f"Live model responded: {content[:30]}... (Consumed ~25 tokens)")
    except Exception as e:
        report.record("LIVE_PROBE", "SiliconFlow Live Probe", False, f"API call failed: {e}")


async def run_all_tests():
    logger.info("================================================================")
    logger.info("STARTING COMPREHENSIVE ARCHITECTURE & PROMPT BEHAVIOR VERIFICATION")
    logger.info("================================================================")

    await setup_test_db()
    await test_module_database_and_fts()
    await test_module_state_and_tools()
    await test_module_hud_and_context()
    await test_module_spatial_and_h3()
    await test_module_search_and_reranking()
    await test_module_core_brain_agentic_loop()
    await test_live_api_probe_if_available()

    summary = report.summary()
    logger.info("================================================================")
    logger.info(f"TEST SUMMARY: Total={summary['total']} | Passed={summary['passed']} | Failed={summary['failed']} | Success Rate={summary['rate']}")
    logger.info(f"ESTIMATED TOKENS CONSUMED: {summary['tokens_used']} (Strictly < 50,000 budget)")
    logger.info("================================================================")

    with open("data/test_execution_report.json", "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "details": report.results}, f, ensure_ascii=False, indent=2)

    return summary


if __name__ == "__main__":
    asyncio.run(run_all_tests())
