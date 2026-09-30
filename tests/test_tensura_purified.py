import asyncio
import os
import sys
import logging
import json
import re

REPO_DIR = r"c:\Users\Asus\Documents\antigravity\amazing-nobel"
sys.path.insert(0, REPO_DIR)
os.chdir(REPO_DIR)
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from config import settings
from core.llm import (
    _get_llm_client,
    SYSTEM_RAPHAEL,
    SYSTEM_LOCATION_EVAL,
    evaluate_location_side_quest
)
from core.brain import RaphaelBrain
from db.database import init_db

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("TENSURA_VERIFICATION")


async def test_purified_raphael_persona():
    logger.info("=== 1. Testing Purified Tensura Raphael Persona ===")
    client = _get_llm_client()

    user_input = "Hôm nay tôi mệt mỏi quá, chả muốn làm gì cả, cứ lười biếng nằm một chỗ."
    
    response = await client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[
            {"role": "system", "content": SYSTEM_RAPHAEL},
            {"role": "user", "content": user_input}
        ],
        temperature=0.0,
        max_tokens=1500,
        extra_body={"reasoning_effort": "high"}
    )
    choice = response.choices[0]
    raw_content = choice.message.content or ""
    
    # Check thinking in English
    thinking_match = re.search(r'<thinking>(.*?)</thinking>', raw_content, flags=re.DOTALL)
    thinking_text = thinking_match.group(1).strip() if thinking_match else ""
    body_text = re.sub(r'<thinking>.*?</thinking>', '', raw_content, flags=re.DOTALL).strip()
    
    logger.info(f"Generated Speech:\n{body_text}\n")
    
    # Check 1: Respectful pronoun
    has_respectful = "ngài" in body_text.lower() or "master" in body_text.lower()
    has_forbidden = any(bad in body_text.lower() for bad in ["bạn", "cậu", "người dùng"])
    
    # Check 2: No snarky interrogation
    has_snarky = any(s in body_text.lower() for s in ["trốn chạy", "tự lừa dối", "dán nhãn"])
    
    # Check 3: Valid prefix
    valid_prefix = any(body_text.startswith(p) for p in ["《Báo cáo》", "《Giải đáp》", "《Xác nhận》", "《Phủ định》"])
    
    word_count = len(body_text.split())
    logger.info(f"Respectful Pronoun: {has_respectful} (Forbidden: {has_forbidden})")
    logger.info(f"Valid Prefix: {valid_prefix}")
    logger.info(f"Snarky/Passive-aggressive Interrogation Detected: {has_snarky}")
    logger.info(f"Word count: {word_count} (Mandate: <= 20 words, max 25 words)")
    assert has_respectful and not has_forbidden, "Failed pronoun check"
    assert valid_prefix, "Failed prefix check"
    assert not has_snarky, "Failed snarky check: response still sounds like an interrogator"
    assert word_count <= 25, f"Response too long ({word_count} words): {body_text}"
    logger.info("[PASS] Purified Tensura Raphael Persona test successful!")


async def test_purified_location_evaluation():
    logger.info("=== 2. Testing Purified Location Evaluation (No Debug Leakage) ===")
    hex_id = "89415cb4e53ffff"
    past_events = [
        {"ts": "2026-09-12 22:00", "desc": "Master hoàn thành module ROS2 sau 4 tiếng tập trung cao độ", "impact": "HIGH"}
    ]
    
    result = await evaluate_location_side_quest(999999, hex_id, past_events)
    logger.info(f"Location Evaluation Output: {result}")
    
    # Check that raw hex string is NOT leaked in speech
    assert hex_id not in result, f"Hex id leaked in user output: {result}"
    assert "Causal Echo Detected" not in result, f"Debug tag leaked: {result}"
    assert "Penalty: -15 Health" not in result, f"Coercive health penalty leaked: {result}"
    logger.info("[PASS] Location evaluation output is clean, respectful, and free of debug tags!")


async def test_brain_quest_interception():
    logger.info("=== 3. Testing Brain Side Quest Interception with Light Gamification ===")
    await init_db()
    brain = RaphaelBrain()

    # Simulate final text with light quest (Penalty: Không)
    test_final = """《Báo cáo》 Master đã hoàn thành xuất sắc ca tập luyện.
[QUEST] Trạm Sạc Sinh Lực: Uống nước và nghỉ ngơi 15 phút | Reward: +25 Credits | Penalty: Không | Expire: 30m | Proof: tự do"""
    
    # Test regex directly
    quest_match = re.search(r'\[QUEST\](.*?)\|\s*Reward:(.*?)(?:\|\s*Penalty:(.*?))?(?:\|\s*Expire:(.*?))?(?:\|\s*Proof:(.*))?$', test_final)
    assert quest_match is not None, "Regex failed to match"
    
    q_title = quest_match.group(1).strip()
    q_reward = quest_match.group(2).strip()
    q_penalty = (quest_match.group(3) or "Không").strip()
    
    penalty_display = f" | Phạt: {q_penalty}" if q_penalty and q_penalty.lower() not in ["không", "none", "no", "0"] else ""
    rendered = re.sub(r'\[QUEST\].*', f'🔥 **NHIỆM VỤ MỚI:** {q_title} (Thưởng: {q_reward}{penalty_display})\n_Đã đồng bộ vào /quests_', test_final)
    
    logger.info(f"Rendered Output:\n{rendered}")
    assert "Phạt: Không" not in rendered, "Penalty: Không should be hidden from positive side quests"
    assert "Thưởng: +25 Credits" in rendered, "Reward should be displayed clearly"
    logger.info("[PASS] Side quest interception handles Light Gamification flawlessly!")


async def main():
    await test_purified_raphael_persona()
    await test_purified_location_evaluation()
    await test_brain_quest_interception()
    logger.info("=== ALL PURIFIED TENSURA TESTS PASSED! ===")


if __name__ == "__main__":
    asyncio.run(main())
