import urllib.request
import json
import os
import sys
from dotenv import load_dotenv

load_dotenv('C:/Users/Asus/Documents/antigravity/amazing-nobel/.env')
api_key = os.environ.get("SILICONFLOW_API_KEY")
if api_key:
    api_key = api_key.strip('"\'')

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

system_prompt = "Bạn là 'Chronicle Inheritor' (Kẻ Kế Thừa Hồi Ký). Nhiệm vụ của bạn là nối tiếp và viết ra các phần của Biên niên sử."

bottom_rules = """
🔥 QUY TẮC DECODE TỐI THƯỢNG:
1. CẤM RÚT GỌN: Mọi bước ngoặt kiến trúc, logic, drama cãi vã, hay bug nghiêm trọng đều phải được viết ra trọn vẹn và chi tiết.
2. ÉP TRÍCH DẪN: Bắt buộc đính kèm trích dẫn (Ví dụ: [Ref: Lời ngài nói] hoặc trích xuất nguyên văn câu chửi/câu khen)."""

CHUNK_SIZE = 600000 # ~150k tokens

for proj in projects:
    print(f"\\n=== ĐANG BĂM NHỎ DỰ ÁN: {proj['name'].upper()} ===", flush=True)
    if not os.path.exists(proj['input_file']): continue
        
    with open(proj['input_file'], 'r', encoding='utf-8') as f:
        text = f.read()
        
    chunks = []
    # Simple chunking
    for i in range(0, len(text), CHUNK_SIZE):
        chunks.append(text[i:i+CHUNK_SIZE])
        
    print(f"-> Đã băm thành {len(chunks)} phần.", flush=True)
    
    # Xóa file cũ nếu có
    with open(proj['output_file'], 'w', encoding='utf-8') as f:
        f.write(f"# BIÊN NIÊN SỬ DỰ ÁN {proj['name'].upper()}\\n\\n")
        
    for idx, chunk in enumerate(chunks):
        print(f"-> Đang gửi Phần {idx+1}/{len(chunks)}...", flush=True)
        prompt = f"[LỆNH HỆ THỐNG]: Dưới đây là dữ liệu Phần {idx+1} của dự án {proj['name'].upper()}.\nHãy tóm tắt cực kỳ chi tiết Phần {idx+1} này thành một chương của Biên niên sử.\n{bottom_rules}\n\n=== DỮ LIỆU KÝ ỨC PHẦN {idx+1} ===\n{chunk}\n=== HẾT DỮ LIỆU ===\n\nBắt đầu xuất dữ liệu chi tiết cho Phần {idx+1}:"
        
        req_data = {
            "model": "deepseek-ai/deepseek-v4.1-flash",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 8000,
            "temperature": 0.25,
            "stream": False
        }
        
        req = urllib.request.Request(
            'https://api.siliconflow.com/v1/chat/completions',
            data=json.dumps(req_data).encode('utf-8'),
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=600) as response:
                res = json.loads(response.read().decode())
                content = res['choices'][0]['message']['content']
                with open(proj['output_file'], 'a', encoding='utf-8') as f:
                    f.write(content + "\\n\\n---\\n\\n")
                print(f"   + Thành công Phần {idx+1}! Ký tự: {len(content)}", flush=True)
        except Exception as e:
            print(f"   + Lỗi ở Phần {idx+1}: {e}", flush=True)

print("\\nHoàn thành toàn bộ Pipeline Chunking!", flush=True)
