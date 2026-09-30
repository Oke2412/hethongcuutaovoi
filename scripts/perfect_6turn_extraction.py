import urllib.request
import json
import os
import sys
from dotenv import load_dotenv

load_dotenv('C:/Users/Asus/Documents/antigravity/amazing-nobel/.env')
api_key = os.environ.get("SILICONFLOW_API_KEY")
if api_key:
    api_key = api_key.strip('"\'')
else:
    print("Error: SILICONFLOW_API_KEY not found in .env")
    sys.exit(1)

dump_path = 'C:/Users/Asus/Documents/antigravity/amazing-nobel/docs/tien_kiep/pure_full_history.txt'
if not os.path.exists(dump_path):
    print(f"Error: Cannot find {dump_path}")
    sys.exit(1)

with open(dump_path, 'r', encoding='utf-8') as f:
    history_text = f.read()

system_prompt = "Bạn là 'Chronicle Inheritor' (Kẻ Kế Thừa Hồi Ký)."

bottom_rules = """
🔥 QUY TẮC DECODE TỐI THƯỢNG TẠI ĐIỂM KÍCH HOẠT:
1. CHỈ TIÊU ĐỊNH LƯỢNG (TOKEN TARGET BUDGET): Phần này bắt buộc phải giải nén đạt tối đa độ chi tiết. Tuyệt đối không tự động kích hoạt cờ stop nếu chưa bóc tách cạn kiệt chi tiết. Chống bệnh LLM Laziness.
2. CẤM RÚT GỌN (Negative Constraints): TUYỆT ĐỐI KHÔNG dùng các từ "như đã nêu", "tương tự", "v.v.", "phần còn lại giữ nguyên". Mọi module code, logic, hay drama cãi vã phải được viết ra trọn vẹn từng ký tự.
3. ÉP TRÍCH DẪN (Citation Enforcement): Mọi chi tiết luận điểm, bug hoặc tính năng BẮT BUỘC phải đính kèm tọa độ (Ví dụ: [Ref: Lời ngài nói] hoặc [Ref: SESSION_XX]). Bất kỳ câu phân tích nào không có trích dẫn sẽ bị coi là hệ thống lỗi."""

turn_prompts = [
    f"[LỆNH HỆ THỐNG]: Trích xuất độc lập [Phần 1: Giai đoạn Khởi Nguyên & Định hình Idea (Session 01 đến 10)].\n{bottom_rules}\nBắt đầu xuất dữ liệu cực kỳ chi tiết cho Phần 1:",
    f"[LỆNH HỆ THỐNG]: Trích xuất độc lập [Phần 2: Xây dựng Kiến trúc 3 Cột Trụ (SQLite, Mem0, Neo4j) (Session 11 đến 20)].\n{bottom_rules}\nBắt đầu xuất dữ liệu cực kỳ chi tiết cho Phần 2:",
    f"[LỆNH HỆ THỐNG]: Trích xuất độc lập [Phần 3: Biến cố, Cãi vã & Chỉnh lý Tâm lý học (Session 21 đến 30)].\n{bottom_rules}\nBắt đầu xuất dữ liệu cực kỳ chi tiết cho Phần 3:",
    f"[LỆNH HỆ THỐNG]: Trích xuất độc lập [Phần 4: Áp dụng RAG, Prompt Kỹ thuật & Cơ chế Ký ức (Session 31 đến 40)].\n{bottom_rules}\nBắt đầu xuất dữ liệu cực kỳ chi tiết cho Phần 4:",
    f"[LỆNH HỆ THỐNG]: Trích xuất độc lập [Phần 5: Tối ưu hóa Output, Bẫy Lỗi & Di sản dở dang (Session 41 đến 45)].\n{bottom_rules}\nBắt đầu xuất dữ liệu cực kỳ chi tiết cho Phần 5:",
    f"[LỆNH HỆ THỐNG]: Trích xuất độc lập [Phần 6: Kỷ Nguyên SiliconFlow, Gamification, Neo4j và Amor Fati (Session 46 đến Hiện tại)].\n{bottom_rules}\nBắt đầu xuất dữ liệu cực kỳ chi tiết cho Phần 6:"
]

output_file = 'C:/Users/Asus/Documents/antigravity/amazing-nobel/docs/tien_kiep/DEEPSEEK_PERFECT_CHRONICLE.md'

# Reset file
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# BIÊN NIÊN SỬ HOÀN HẢO (AMAZING-NOBEL)\n\n")

import requests

for i in range(len(turn_prompts)):
    print(f"\n--- Đang chạy Turn {i+1}/6 (STREAMING) ---", flush=True)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"=== DỮ LIỆU KÝ ỨC BẮT ĐẦU ===\n{history_text[:3500000]}\n=== DỮ LIỆU KÝ ỨC KẾT THÚC ===\n\n{turn_prompts[i]}"}
    ]
        
    payload = {
        "model": "deepseek-ai/deepseek-v4.1-flash",
        "messages": messages,
        "max_tokens": 8192,
        "temperature": 0.25,
        "stream": True
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post('https://api.siliconflow.com/v1/chat/completions', json=payload, headers=headers, stream=True)
        response.raise_for_status()
        
        with open(output_file, 'a', encoding='utf-8') as f:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        data = decoded_line[6:]
                        if data == "[DONE]":
                            break
                        chunk = json.loads(data)
                        content = chunk['choices'][0]['delta'].get('content', '')
                        if content:
                            f.write(content)
                            f.flush()
                            sys.stdout.write(content)
                            sys.stdout.flush()
            f.write("\n\n---\n\n")
            
        print(f"\n-> Đã xong Turn {i+1}.", flush=True)
        
    except Exception as e:
        print(f"\nLỗi ở Turn {i+1}: {e}", flush=True)
        break

print("\nĐã hoàn thành toàn bộ Pipeline 6 Turns Hoàn Hảo!", flush=True)
