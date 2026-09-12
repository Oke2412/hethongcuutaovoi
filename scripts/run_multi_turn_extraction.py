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

dump_path = 'C:/Users/Asus/.gemini/antigravity/brain/600c73f3-8a09-4bca-a213-95224d8b75a6/scratch/full_history_dump.txt'
with open(dump_path, 'r', encoding='utf-8') as f:
    history_text = f.read()

system_prompt = "Bạn là 'Chronicle Inheritor' (Kẻ Kế Thừa Hồi Ký)."

bottom_rules = """
⚠️ QUY TẮC DECODE TỐI THƯỢNG TẠI ĐIỂM KÍCH HOẠT:
1. CHỈ TIÊU ĐỊNH LƯỢNG (TOKEN TARGET BUDGET): Phần này bắt buộc phải giải nén đạt tối thiểu 15,000 token output. Tuyệt đối không tự động kích hoạt cờ stop nếu chưa bóc tách cạn kiệt chi tiết.
2. CẤM RÚT GỌN (Negative Constraints): TUYỆT ĐỐI KHÔNG dùng các từ "như đã nêu", "tương tự", "v.v.", "phần còn lại giữ nguyên". Mọi module code, logic, hay drama cãi vã phải được viết ra trọn vẹn từng ký tự.
3. ÉP TRÍCH DẪN (Citation Enforcement): Mọi chi tiết luận điểm, bug hoặc tính năng BẮT BUỘC phải đính kèm tọa độ (Ví dụ: [Ref: SESSION_05]). Bất kỳ câu phân tích nào không có trích dẫn sẽ bị coi là hệ thống lỗi."""

turn_prompts = [
    f"[LỆNH HỆ THỐNG]: Trích xuất độc lập [Phần 1: Giai đoạn Khởi Nguyên & Định hình Idea (Session 01 đến 10)].\n{bottom_rules}\nBắt đầu xuất dữ liệu cực kỳ chi tiết cho Phần 1:",
    f"[LỆNH HỆ THỐNG]: Trích xuất độc lập [Phần 2: Xây dựng Kiến trúc 3 Cột Trụ (SQLite, Mem0, Neo4j) (Session 11 đến 20)].\n{bottom_rules}\nBắt đầu xuất dữ liệu cực kỳ chi tiết cho Phần 2:",
    f"[LỆNH HỆ THỐNG]: Trích xuất độc lập [Phần 3: Biến cố, Cãi vã & Chỉnh lý Tâm lý học (Session 21 đến 30)].\n{bottom_rules}\nBắt đầu xuất dữ liệu cực kỳ chi tiết cho Phần 3:",
    f"[LỆNH HỆ THỐNG]: Trích xuất độc lập [Phần 4: Áp dụng RAG, Prompt Kỹ thuật & Cơ chế Ký ức (Session 31 đến 40)].\n{bottom_rules}\nBắt đầu xuất dữ liệu cực kỳ chi tiết cho Phần 4:",
    f"[LỆNH HỆ THỐNG]: Trích xuất độc lập [Phần 5: Tối ưu hóa Output, Bẫy Lỗi & Di sản dở dang (Session 41 đến 48)].\n{bottom_rules}\nBắt đầu xuất dữ liệu cực kỳ chi tiết cho Phần 5:"
]

output_file = 'C:/Users/Asus/.gemini/antigravity/brain/600c73f3-8a09-4bca-a213-95224d8b75a6/MASTER_TIEN_KIEP.md'

print("Tiếp tục Kiến trúc Độc lập từ Turn 3...", flush=True)

for i in range(3, 5): # Chạy từ Turn 3 (index 2)
    print(f"\n--- Đang chạy Turn {i+1}/5 ---", flush=True)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"=== DỮ LIỆU KÝ ỨC BẮT ĐẦU ===\n{history_text[:3000000]}\n=== DỮ LIỆU KÝ ỨC KẾT THÚC ===\n\n{turn_prompts[i]}"}
    ]
        
    req_data = {
        "model": "deepseek-ai/deepseek-v4.1-flash",
        "messages": messages,
        "max_tokens": 20000,
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
