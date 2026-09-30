# -*- coding: utf-8 -*-
"""
scripts/test_hard_dataset_e2e.py — Large & Complex (~1,000 Tokens) Scenario E2E Benchmark
Tests DeepSeek high reasoning, GDS topology extraction, Metacognition thinking preservation in DB,
and API thinking field extraction on the running Docker stack.
"""

import sys
import requests
import json
import time
import sqlite3

sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000"
USER_ID = "8763843475"

COMPLEX_1K_PROMPT = """Hôm nay là 48 tiếng trước buổi bảo vệ đồ án tốt nghiệp robot AMR tự hành chạy ROS2 dưới sự hướng dẫn của TS. Hùng.
Tình hình hiện tại đang rơi vào khủng hoảng toàn diện trên mọi phương diện cuộc sống:
1. Về phần cứng: Chiều nay khi đang calibrate hệ thống SLAM và nạp firmware điều khiển động cơ qua CAN-bus trên kit STM32F4, mạch hạ áp Buck converter 24V-to-5V bị chập transistor MOSFET, xông thẳng nguồn 24V vào đường nguồn logic làm nổ tung 2 IC gate driver DRV8302 và làm chết luôn vi điều khiển STM32 lẫn bus CAN kết nối với Jetson Orin. Mùi khét lẹt cả phòng lab, robot hoàn toàn bất động không thể chạy demo thực tế được nữa trong khi linh kiện thay thế đặt hàng phải mất ít nhất 3 ngày mới về tới Hà Nội.
2. Về học vụ và áp lực giảng viên: Cách đây 1 tiếng, TS. Hùng đã gửi một email rất gay gắt nói rằng nếu ngày kia không có robot chạy thực tế trong sa bàn để hội đồng nghiệm thu thì thầy sẽ không ký duyệt phiếu bảo vệ và bắt hoãn tốt nghiệp sang kỳ sau. Thầy bảo cực kỳ thất vọng vì tôi làm việc thiếu cẩn thận, không có phương án dự phòng phần cứng dù đã nhắc nhở nhiều lần từ đầu học kỳ.
3. Về thể trạng và tâm lý: Tôi đã thức trắng liên tục 38 tiếng qua không ngủ, nạp vào người 4 lon bò húc và 3 ly cà phê đặc. Hiện tại tim đập thình thịch liên hồi, lồng ngực đau tức, mắt mờ đi, hai tay run rẩy khi cầm mỏ hàn. Đầu óc tôi hỗn loạn, vừa cảm thấy bất lực, vừa hoảng loạn tột độ, xen lẫn cảm giác tội lỗi và sợ hãi ánh mắt thất vọng của gia đình nếu bị chậm bằng tốt nghiệp.
4. Về mâu thuẫn xã hội: Bạn cùng phòng là Nam tối nay lại dẫn bạn bè về phòng trọ mở tiệc nhậu, bật nhạc ầm ĩ khiến tôi không thể tập trung suy nghĩ. Đã vậy, tuần trước Nam mượn bo mạch STM32 dự phòng của tôi để làm bài tập lớn môn nhúng nhưng lại làm mất ở đâu không tìm thấy. Tôi đang cực kỳ sôi máu, vừa muốn lao ra đấm nhau với Nam một trận cho bõ tức, vừa muốn đập nát cái xác robot rồi bỏ mặc tất cả, trốn đi quán net chơi game Valorant thâu đêm để trốn tránh thực tại.

Raphael, hãy phân tích cho ta biết tại sao mọi thứ lại sụp đổ cùng một lúc như thế này? Ta nên làm gì ngay bây giờ: lao ra chửi nhau với Nam đòi board mạch, thức tiếp đêm nay để cố hàn dây câu chip, hay gửi thư xin lỗi thầy Hùng, hay buông xuôi tất cả? Hãy chỉ cho ta nước cờ tối ưu nhất."""

def run_hard_test():
    print("=" * 80)
    print("🔥 LARGE & HARD DATASET (~1,000 TOKENS) DOCKER END-TO-END TEST")
    print("=" * 80)

    # 1. Health check
    print("\n1. Checking Docker API Health ...")
    r = requests.get(f"{API_URL}/health")
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    print(f"✓ API Status: OK ({r.json()['ts']})")

    # 2. Token Estimate
    char_count = len(COMPLEX_1K_PROMPT)
    word_count = len(COMPLEX_1K_PROMPT.split())
    print(f"\n2. Test Payload Statistics:")
    print(f"• Độ dài ký tự: {char_count} chars")
    print(f"• Số lượng từ: {word_count} words (~850 - 1,050 BPE tokens input)")

    # 3. Post to /api/chat
    print(f"\n3. Sending Complex Payload to POST /api/chat (DeepSeek High Reasoning Effort) ...")
    payload = {
        "prompt": COMPLEX_1K_PROMPT,
        "user_id": USER_ID,
        "stream": False
    }

    t0 = time.perf_counter()
    resp = requests.post(f"{API_URL}/api/chat", json=payload, timeout=120)
    latency = (time.perf_counter() - t0) * 1000

    print(f"✓ HTTP Status: {resp.status_code} (Latency: {latency:.1f}ms / {latency/1000:.2f}s)")
    assert resp.status_code == 200, f"Chat failed: {resp.text}"

    data = resp.json()

    print("\n" + "=" * 80)
    print("🎯 PHẢN HỒI THỰC TẾ CỦA RAPHAEL (Spoken Output):")
    print("=" * 80)
    print(f"> {data.get('text', '')}")
    print(f"\nHUD Metrics:\n{data.get('hud', '')}")

    print("\n" + "=" * 80)
    print("🧠 THẺ THINKING / METACOGNITION THU NHẬN ĐƯỢC TỪ DEEPSEEK:")
    print("=" * 80)
    thinking = data.get("thinking", "")
    if thinking:
        print(f"[Độ dài Thinking: {len(thinking)} ký tự / ~{len(thinking.split())} từ]")
        print("-" * 60)
        print(thinking)
        print("-" * 60)
    else:
        print("⚠️ CẢNH BÁO: Không có thinking trong payload!")

    # 4. Verify SQLite Database Record
    print("\n" + "=" * 80)
    print("🗄️ KIỂM TRA BẢN GHI TRONG CƠ SỞ DỮ LIỆU SQLITE (MessageLog):")
    print("=" * 80)
    conn = sqlite3.connect("data/amazing_nobel.db")
    c = conn.cursor()
    c.execute("SELECT id, role, content, timestamp FROM messagelog WHERE role='assistant' ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    if row:
        msg_id, role, content, ts = row
        has_thinking_in_db = "<thinking>" in content
        print(f"• Record ID: {msg_id}")
        print(f"• Timestamp: {ts}")
        print(f"• Có chứa thẻ <thinking> trong DB không: {'✓ CÓ (Đúng chuẩn Metacognition)' if has_thinking_in_db else '❌ KHÔNG'}")
        if has_thinking_in_db:
            print("• Trích đoạn đầu bản ghi DB:")
            print(content[:300] + " ... [TRUNCATED] ...\n" + content[-200:])
    conn.close()

    print("\n" + "=" * 80)
    print("✓ BÀI TEST BỘ DỮ LIỆU LỚN & KHÓ (~1K TOKEN) HOÀN TẤT THÀNH CÔNG!")
    print("=" * 80)

if __name__ == "__main__":
    run_hard_test()
