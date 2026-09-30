import json
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv('C:/Users/Asus/Documents/antigravity/amazing-nobel/.env')
api_key = os.environ.get("SILICONFLOW_API_KEY")
if api_key:
    api_key = api_key.strip('"\'')
else:
    print("Error: SILICONFLOW_API_KEY not found in .env")
    sys.exit(1)

projects = [
    {
        "name": "amazing-nobel",
        "input_file": "C:/Users/Asus/Documents/antigravity/amazing-nobel/docs/tien_kiep/pure_full_history.txt",
        "output_file": "C:/Users/Asus/Documents/antigravity/amazing-nobel/docs/tien_kiep/DEEPSEEK_CHRONICLE_AMAZING_NOBEL.md"
    },
    {
        "name": "visaireal",
        "input_file": "C:/Users/Asus/Documents/antigravity/amazing-nobel/docs/tien_kiep/pure_history_visaireal.txt",
        "output_file": "C:/Users/Asus/Documents/antigravity/amazing-nobel/docs/tien_kiep/DEEPSEEK_CHRONICLE_VISAIREAL.md"
    }
]

system_prompt = "Bạn là 'Chronicle Inheritor' (Kẻ Kế Thừa Hồi Ký). Dưới đây là dữ liệu toàn bộ lịch sử."

bottom_rules = """
🔥 QUY TẮC DECODE TỐI THƯỢNG TẠI ĐIỂM KÍCH HOẠT:
1. CẤM RÚT GỌN: KHÔNG dùng các từ "như đã nêu", "tương tự". Mọi bước ngoặt kiến trúc, logic, drama cãi vã, hay bug nghiêm trọng đều phải được viết ra trọn vẹn và chi tiết.
2. ÉP TRÍCH DẪN: Bắt buộc đính kèm trích dẫn (Ví dụ: [Ref: Lời ngài nói] hoặc trích xuất nguyên văn câu chửi/câu khen)."""

for proj in projects:
    print(f"\\n=== ĐANG XỬ LÝ TRỰC TIẾP (STREAMING): {proj['name'].upper()} ===", flush=True)
    if not os.path.exists(proj['input_file']): continue
        
    with open(proj['input_file'], 'r', encoding='utf-8') as f:
        history_text = f.read()
        
    prompt = f"[LỆNH HỆ THỐNG]: Trích xuất độc lập Biên niên sử vĩ đại của dự án {proj['name'].upper()}.\n{bottom_rules}\n\n=== DỮ LIỆU KÝ ỨC BẮT ĐẦU ===\n{history_text[:3500000]}\n=== DỮ LIỆU KÝ ỨC KẾT THÚC ===\n\nBắt đầu xuất dữ liệu cực kỳ chi tiết cho dự án {proj['name'].upper()}:"
    
    payload = {
        "model": "deepseek-ai/deepseek-v4.1-flash",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 8192,
        "temperature": 0.25,
        "stream": True  # Enable streaming to bypass Nginx gateway timeout
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post('https://api.siliconflow.com/v1/chat/completions', json=payload, headers=headers, stream=True)
        response.raise_for_status()
        
        with open(proj['output_file'], 'w', encoding='utf-8') as f:
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
        print(f"\\n-> Đã xong {proj['name']}.", flush=True)
    except Exception as e:
        print(f"\\nLỗi ở dự án {proj['name']}: {e}", flush=True)

print("\\nĐã hoàn thành toàn bộ Pipeline Streaming!", flush=True)
