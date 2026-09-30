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

dump_path = 'C:/Users/Asus/Documents/antigravity/amazing-nobel/docs/tien_kiep/raw_chat_delta.txt'
with open(dump_path, 'r', encoding='utf-8') as f:
    history_text = f.read()

system_prompt = "Bạn là 'Chronicle Inheritor' (Kẻ Kế Thừa Hồi Ký)."

bottom_rules = """
🔥 QUY TẮC DECODE TỐI THƯỢNG TẠI ĐIỂM KÍCH HOẠT:
1. CHỈ TIÊU ĐỊNH LƯỢNG (TOKEN TARGET BUDGET): Phần này bắt buộc phải giải nén đạt tối thiểu 15,000 token output. Tuyệt đối không tự động kích hoạt cờ stop nếu chưa bóc tách cạn kiệt chi tiết.
2. CẤM RÚT GỌN (Negative Constraints): TUYỆT ĐỐI KHÔNG dùng các từ "như đã nêu", "tương tự", "v.v.", "phần còn lại giữ nguyên". Mọi module code, logic, hay drama cãi vã phải được viết ra trọn vẹn từng ký tự.
3. ÉP TRÍCH DẪN (Citation Enforcement): Mọi chi tiết luận điểm, bug hoặc tính năng BẮT BUỘC phải đính kèm tựa độ (Ví dụ: [Ref: SESSION_05]). Bất kỳ câu phân tích nào không có trích dẫn sẽ bị coi là hệ thống lỗi."""

turn_prompts = [
    f"[LỆNH HỆ THỐNG]: Trích xuất độc lập [Phần 1].\n{bottom_rules}\nBắt đầu:",
    f"[LỆNH HỆ THỐNG]: Trích xuất độc lập [Phần 2].\n{bottom_rules}\nBắt đầu:",
    f"[LỆNH HỆ THỐNG]: Trích xuất độc lập [Phần 3].\n{bottom_rules}\nBắt đầu:",
    f"[LỆNH HỆ THỐNG]: Trích xuất độc lập [Phần 4].\n{bottom_rules}\nBắt đầu:",
    f"[LỆNH HỆ THỐNG]: Trích xuất độc lập [Phần 5].\n{bottom_rules}\nBắt đầu:",
    f"[LỆNH HỆ THỐNG]: Trích xuất độc lập [Phần 6: Kỷ Nguyên SiliconFlow, Gamification, Neo4j và Amor Fati (Từ Session 45 đến hiện tại)].\n{bottom_rules}\nBắt đầu xuất dữ liệu cực kỳ chi tiết cho Phần 6:"
]

output_file = 'C:/Users/Asus/Documents/antigravity/amazing-nobel/docs/tien_kiep/DEEPSEEK_PHAN_6.md'

print("Tiếp tục Kiến trúc Độc lập...", flush=True)

for i in range(5, 6): # Chỉ chạy Turn 6
    print(f"\n--- Đang chạy Turn {i+1}/6 ---", flush=True)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"=== DỮ LIỆU KÝ ỨC BẮT ĐẦU ===\n{history_text[:3000000]}\n=== DỮ LIỆU KÝ ỨC KẾT THÚC ===\n\n{turn_prompts[i]}"}
    ]
        
    req_data = {
        "model": "deepseek-ai/deepseek-v4.1-flash",
        "messages": messages,
        "max_tokens": 8000,
        "temperature": 0.25,
        "presence_penalty": 0.15,
        "reasoning_effort": "none",
        "stream": False
    }
    
    req = urllib.request.Request(
        'https://api.siliconflow.com/v1/chat/completions',
        data=json.dumps(req_data).encode('utf-8'),
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=600) as response:
            res_data = json.loads(response.read().decode())
            content = res_data['choices'][0]['message']['content']
            
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(content + "\n\n")
                
            print(f"-> Đã xong Turn {i+1}. Số ký tự sinh ra: {len(content)}", flush=True)
            
    except Exception as e:
        print(f"Lỗi ở Turn {i+1}: {e}", flush=True)
        break

print("\nĐã hoàn thành toàn bộ Pipeline!", flush=True)
