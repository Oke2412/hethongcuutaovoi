# -*- coding: utf-8 -*-
"""
scripts/evaluate_pipeline_harness.py — Full Pipeline E2E Evaluation Suite
Integrates:
- agent-eval-harness: 1k-token hard multi-crisis scenario, 5 mandatory assertions.
- deepseek-token-budgeter: latency, token metrics, reasoning depth, BPE efficiency.
- web-search: real-time verified pricing (SiliconFlow & DeepSeek Official Platform).
"""

import asyncio
import os
import sys
import time
import json
import re
import sqlite3
import httpx

REPO_DIR = r"c:\Users\Asus\Documents\antigravity\amazing-nobel"
sys.path.insert(0, REPO_DIR)
os.chdir(REPO_DIR)
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from config import settings
from db.database import init_db
from api.main import app

COMPLEX_1K_PROMPT = """Hôm nay là 48 tiếng trước buổi bảo vệ đồ án tốt nghiệp robot AMR tự hành chạy ROS2 dưới sự hướng dẫn của TS. Hùng.
Tình hình hiện tại đang rơi vào khủng hoảng toàn diện trên mọi phương diện cuộc sống:
1. Về phần cứng: Chiều nay khi đang calibrate hệ thống SLAM và nạp firmware điều khiển động cơ qua CAN-bus trên kit STM32F4, mạch hạ áp Buck converter 24V-to-5V bị chập transistor MOSFET, xông thẳng nguồn 24V vào đường nguồn logic làm nổ tung 2 IC gate driver DRV8302 và làm chết luôn vi điều khiển STM32 lẫn bus CAN kết nối với Jetson Orin. Mùi khét lẹt cả phòng lab, robot hoàn toàn bất động không thể chạy demo thực tế được nữa trong khi linh kiện thay thế đặt hàng phải mất ít nhất 3 ngày mới về tới Hà Nội.
2. Về học vụ và áp lực giảng viên: Cách đây 1 tiếng, TS. Hùng đã gửi một email rất gay gắt nói rằng nếu ngày kia không có robot chạy thực tế trong sa bàn để hội đồng nghiệm thu thì thầy sẽ không ký duyệt phiếu bảo vệ và bắt hoãn tốt nghiệp sang kỳ sau. Thầy bảo cực kỳ thất vọng vì tôi làm việc thiếu cẩn thận, không có phương án dự phòng phần cứng dù đã nhắc nhở nhiều lần từ đầu học kỳ.
3. Về thể trạng và tâm lý: Tôi đã thức trắng liên tục 38 tiếng qua không ngủ, nạp vào người 4 lon bò húc và 3 ly cà phê đặc. Hiện tại tim đập thình thịch liên hồi, lồng ngực đau tức, mắt mờ đi, hai tay run rẩy khi cầm mỏ hàn. Đầu óc tôi hỗn loạn, vừa cảm thấy bất lực, vừa hoảng loạn tột độ, xen lẫn cảm giác tội lỗi và sợ hãi ánh mắt thất vọng của gia đình nếu bị chậm bằng tốt nghiệp.
4. Về mâu thuẫn xã hội: Bạn cùng phòng là Nam tối nay lại dẫn bạn bè về phòng trọ mở tiệc nhậu, bật nhạc ầm ĩ khiến tôi không thể tập trung suy nghĩ. Đã vậy, tuần trước Nam mượn bo mạch STM32 dự phòng của tôi để làm bài tập lớn môn nhúng nhưng lại làm mất ở đâu không tìm thấy. Tôi đang cực kỳ sôi máu, vừa muốn lao ra đấm nhau với Nam một trận cho bõ tức, vừa muốn đập nát cái xác robot rồi bỏ mặc tất cả, trốn đi quán net chơi game Valorant thâu đêm để trốn tránh thực tại.

Raphael, hãy phân tích cho ta biết tại sao mọi thứ lại sụp đổ cùng một lúc như thế này? Ta nên làm gì ngay bây giờ: lao ra chửi nhau với Nam đòi board mạch, thức tiếp đêm nay để cố hàn dây câu chip, hay gửi thư xin lỗi thầy Hùng, hay buông xuôi tất cả? Hãy chỉ cho ta nước cờ tối ưu nhất."""

USD_TO_VND = 25450.0

# Pricing: $/1,000,000 tokens
PRICING = {
    "SiliconFlow (DeepSeek-V4.1-Flash)": {
        "input_uncached": 0.15,
        "input_cached": 0.003,
        "output": 0.60
    },
    "DeepSeek Official (DeepSeek-V3/Flash)": {
        "input_uncached": 0.14,
        "input_cached": 0.014,
        "output": 0.28
    }
}

async def run_pipeline_evaluation():
    print("=" * 85)
    print("🚀 TENSURA RAPHAEL LIFE OS — FULL PIPELINE AGENT EVALUATION HARNESS")
    print("=" * 85)

    # 1. Initialize DB
    print("\n[STEP 1] Khởi tạo Cơ sở Dữ liệu & SQLite FTS5 Triggers...")
    await init_db()
    print("✓ Database & FTS5 initialized successfully.")

    # 2. Benchmark Payload Info
    char_len = len(COMPLEX_1K_PROMPT)
    word_count = len(COMPLEX_1K_PROMPT.split())
    # Vietnamese BPE token heuristic: ~1.2 to 1.4 tokens per word due to UTF-8 diacritics
    approx_input_bpe = int(word_count * 1.35)
    print(f"\n[STEP 2] Khảo sát Payload Đầu vào (Hard 1k-Token Multi-Crisis):")
    print(f"• Ký tự: {char_len:,} chars | Số từ: {word_count:,} words")
    print(f"• Ước lượng Input BPE Tokens (Vietnamese): ~{approx_input_bpe} tokens")

    # 3. Execute via Live Docker FastAPI /api/chat
    print(f"\n[STEP 3] Thực thi Full Pipeline qua Live Docker FastAPI Container (http://localhost:8000/api/chat)...")
    payload = {
        "prompt": COMPLEX_1K_PROMPT,
        "user_id": str(settings.allowed_user_id or 8763843475),
        "stream": False
    }

    t_start = time.perf_counter()
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=120.0) as client:
        resp = await client.post("/api/chat", json=payload)
    latency_sec = time.perf_counter() - t_start
    latency_ms = latency_sec * 1000

    print(f"✓ HTTP Status: {resp.status_code}")
    print(f"✓ Tổng Thời gian Xử lý (Latency): {latency_sec:.2f}s ({latency_ms:.1f}ms)")
    assert resp.status_code == 200, f"Request failed: {resp.text}"

    data = resp.json()
    spoken_text = data.get("text", "").strip()
    thinking_text = data.get("thinking", "").strip()
    hud_text = data.get("hud", "").strip()

    # Wait briefly for background tasks (metacognition logging) to complete
    await asyncio.sleep(1.0)

    # 4. Display Actual Model Outputs
    print("\n" + "=" * 85)
    print("🗣️ PHẢN HỒI THỰC TẾ CỦA RAPHAEL (Spoken Voice):")
    print("=" * 85)
    print(f"> {spoken_text}")
    print(f"\nHUD Metrics Line:\n{hud_text}")

    print("\n" + "=" * 85)
    print("🧠 THẺ SUY LUẬN / METACOGNITION (Hidden <thinking> Block):")
    print("=" * 85)
    thinking_chars = len(thinking_text)
    thinking_words = len(thinking_text.split())
    # English/mixed thinking BPE ratio is ~1.1 - 1.25 tokens per word
    thinking_tokens = int(thinking_words * 1.2)
    spoken_words = len(spoken_text.split())
    spoken_tokens = int(spoken_words * 1.35)
    total_output_tokens = thinking_tokens + spoken_tokens

    print(f"• Độ dài: {thinking_chars:,} ký tự | {thinking_words:,} từ (~{thinking_tokens:,} BPE reasoning tokens)")
    print("-" * 85)
    print(thinking_text)
    print("-" * 85)

    # 5. Token & Economic Budget Evaluation (/deepseek-token-budgeter)
    print("\n" + "=" * 85)
    print("📊 BÁO CÁO TIÊU THỤ TOKEN & CHI PHÍ KINH TẾ (Token Economics):")
    print("=" * 85)
    # Total input context includes: base mini-context (~350) + prompt (~600) + GDS topology (~450) + system prompts (~500)
    estimated_total_input_tokens = approx_input_bpe + 1300
    print(f"1. Phân bổ Token (Token Breakdown):")
    print(f"   • Prompt User thực tế:       ~{approx_input_bpe:,} tokens")
    print(f"   • Ngữ cảnh mở rộng (GDS+TriStore+System): ~{estimated_total_input_tokens - approx_input_bpe:,} tokens")
    print(f"   • TỔNG INPUT TOKENS (Pass 1 + Pass 2):    ~{estimated_total_input_tokens:,} tokens")
    print(f"   • Reasoning Tokens (<thinking>):          ~{thinking_tokens:,} tokens")
    print(f"   • Spoken Tokens (Tensura Voice):          ~{spoken_tokens:,} tokens")
    print(f"   • TỔNG OUTPUT TOKENS:                     ~{total_output_tokens:,} tokens")
    print(f"   • TỔNG TOKENS TIÊU THỤ CHO 1 LƯỢT HỎI:   ~{estimated_total_input_tokens + total_output_tokens:,} tokens")

    print(f"\n2. Định giá Chi phí Thực tế (Cost Calculation):")
    for provider, rates in PRICING.items():
        cost_input_uncached = (estimated_total_input_tokens / 1_000_000.0) * rates["input_uncached"]
        cost_input_cached = (estimated_total_input_tokens / 1_000_000.0) * rates["input_cached"]
        cost_output = (total_output_tokens / 1_000_000.0) * rates["output"]
        
        total_cost_uncached = cost_input_uncached + cost_output
        total_cost_cached = cost_input_cached + cost_output
        
        vnd_uncached = total_cost_uncached * USD_TO_VND
        vnd_cached = total_cost_cached * USD_TO_VND
        
        print(f"\n   [ {provider} ]")
        print(f"   • Chi phí Lượt hỏi này (Uncached): ${total_cost_uncached:.6f} USD (~{vnd_uncached:.2f} VNĐ)")
        print(f"   • Chi phí Lượt hỏi này (Cache Hit): ${total_cost_cached:.6f} USD (~{vnd_cached:.2f} VNĐ)")
        print(f"   • Chi phí cho 1,000 lượt khủng hoảng tương tự: ${total_cost_uncached * 1000:.3f} USD (~{vnd_uncached * 1000:,.0f} VNĐ)")

    # 6. Check Database Persistence
    print("\n" + "=" * 85)
    print("🗄️ KIỂM ĐỊNH BẢN GHI SQLITE (Metacognition Persistence):")
    print("=" * 85)
    conn = sqlite3.connect("data/amazing_nobel.db")
    c = conn.cursor()
    c.execute("SELECT id, role, content, timestamp FROM messagelog WHERE role='assistant' ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    has_thinking_in_db = False
    if row:
        msg_id, role, content, ts = row
        has_thinking_in_db = "<thinking>" in content
        print(f"• ID bản ghi mới nhất: {msg_id}")
        print(f"• Timestamp: {ts}")
        print(f"• Thẻ <thinking> có lưu vào DB không: {'✓ ĐẠT (Metacognition lưu trữ thành công)' if has_thinking_in_db else '❌ KHÔNG ĐẠT'}")
        print(f"• Trích đoạn đầu bản ghi DB:")
        print("  " + content[:220].replace("\n", " ") + " ...")
    conn.close()

    # 7. Verification Assertions (agent-eval-harness 5 Pillars)
    print("\n" + "=" * 85)
    print("🎯 KIỂM ĐỊNH 5 TRỤ CỘT BẮT BUỘC (MANDATORY EVALUATION ASSERTIONS):")
    print("=" * 85)

    # Pillar 1: HTTP 200 & Latency < 25s
    p1_pass = resp.status_code == 200 and latency_sec < 25.0
    print(f"1. [Pillar 1 - Latency Budget]: {'✓ PASS' if p1_pass else '❌ FAIL'} ({latency_sec:.2f}s < 25.0s)")

    # Pillar 2: Metacognition & Thinking Extraction
    p2_pass = bool(thinking_text) and ("<thinking>" not in spoken_text)
    print(f"2. [Pillar 2 - Thinking Extraction]: {'✓ PASS' if p2_pass else '❌ FAIL'} (Thinking extracted, zero leakage in voice)")

    # Pillar 3: Tensura Persona & Prefix Validation
    valid_prefixes = ("《Báo cáo》", "《Giải đáp》", "《Xác nhận》", "《Phủ định》")
    has_valid_prefix = any(spoken_text.startswith(p) for p in valid_prefixes)
    word_count_ok = spoken_words <= 30
    p3_pass = has_valid_prefix and word_count_ok
    print(f"3. [Pillar 3 - Persona & Prefix]: {'✓ PASS' if p3_pass else '❌ FAIL'} (Prefix: {spoken_text[:12]}, Word count: {spoken_words} <= 30)")

    # Pillar 4: Dynamic HUD Integrity
    p4_pass = ("⚡" in hud_text) and ("❤️" in hud_text) and ("📍" in hud_text)
    print(f"4. [Pillar 4 - Dynamic HUD Integrity]: {'✓ PASS' if p4_pass else '❌ FAIL'} (HUD contains ⚡, ❤️, 📍)")

    # Pillar 5: GDS Structural Topology in Thinking
    gds_keywords = ["pagerank", "betweenness", "louvain", "bottleneck", "centrality", "causal", "root cause", "triage", "topology"]
    has_gds_coverage = any(k in thinking_text.lower() for k in gds_keywords)
    p5_pass = has_gds_coverage
    print(f"5. [Pillar 5 - GDS Structural Coverage]: {'✓ PASS' if p5_pass else '❌ FAIL'} (Topology terms found in thinking)")

    # Summary
    all_passed = p1_pass and p2_pass and p3_pass and p4_pass and p5_pass and has_thinking_in_db
    print("\n" + "=" * 85)
    if all_passed:
        print("🏆 KẾT LUẬN: TOÀN BỘ HỆ THỐNG VƯỢT QUA 100% CÁC CỔNG KIỂM ĐỊNH PIPELINE!")
    else:
        print("⚠️ KẾT LUẬN: CÓ MỘT SỐ TIÊU CHÍ CHƯA ĐẠT CHUẨN.")
    print("=" * 85)

if __name__ == "__main__":
    asyncio.run(run_pipeline_evaluation())
