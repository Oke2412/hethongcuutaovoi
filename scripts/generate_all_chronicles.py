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

projects = [
    {
        "name": "amazing-nobel",
        "input_file": "C:/Users/Asus/Documents/antigravity/amazing-nobel/docs/tien_kiep/pure_full_history.txt",
        "output_file": "C:/Users/Asus/Documents/antigravity/amazing-nobel/docs/tien_kiep/DEEPSEEK_CHRONICLE_AMAZING_NOBEL.md"
    },
    {
        "name": "sttap",
        "input_file": "C:/Users/Asus/Documents/antigravity/amazing-nobel/docs/tien_kiep/pure_history_sttap.txt",
        "output_file": "C:/Users/Asus/Documents/antigravity/amazing-nobel/docs/tien_kiep/DEEPSEEK_CHRONICLE_STTAP.md"
    },
    {
        "name": "visaireal",
        "input_file": "C:/Users/Asus/Documents/antigravity/amazing-nobel/docs/tien_kiep/pure_history_visaireal.txt",
        "output_file": "C:/Users/Asus/Documents/antigravity/amazing-nobel/docs/tien_kiep/DEEPSEEK_CHRONICLE_VISAIREAL.md"
    }
]

system_prompt = "Bạn là 'Chronicle Inheritor' (Kẻ Kế Thừa Hồi Ký)."

bottom_rules = """
🔥 QUY TẮC DECODE TỐI THƯỢNG TẠI ĐIỂM KÍCH HOẠT:
1. Bạn phải tóm tắt lại TOÀN BỘ lịch sử phát triển của dự án này từ thuở sơ khai đến hiện tại, chia thành các chương/phần logic theo tiến trình thời gian.
2. CẤM RÚT GỌN: KHÔNG dùng các từ "như đã nêu", "tương tự". Mọi bước ngoặt kiến trúc, logic, drama cãi vã, hay bug nghiêm trọng đều phải được viết ra trọn vẹn và chi tiết.
3. ÉP TRÍCH DẪN: Mọi chi tiết luận điểm bắt buộc phải đính kèm trích dẫn (Ví dụ: [Ref: Lời ngài nói] hoặc trích xuất nguyên văn câu chửi/câu khen)."""

for proj in projects:
    print(f"\\n=== ĐANG XỬ LÝ DỰ ÁN: {proj['name'].upper()} ===", flush=True)
    if not os.path.exists(proj['input_file']):
        print(f"Bỏ qua vì không tìm thấy file {proj['input_file']}")
        continue
        
    with open(proj['input_file'], 'r', encoding='utf-8') as f:
        history_text = f.read()
        
    prompt = f"[LỆNH HỆ THỐNG]: Trích xuất độc lập Biên niên sử vĩ đại của dự án {proj['name'].upper()}.\n{bottom_rules}\n\n=== DỮ LIỆU KÝ ỨC BẮT ĐẦU ===\n{history_text[:3500000]}\n=== DỮ LIỆU KÝ ỨC KẾT THÚC ===\n\nBắt đầu xuất dữ liệu cực kỳ chi tiết cho toàn bộ lịch sử dự án {proj['name'].upper()}:"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
        
    req_data = {
        "model": "deepseek-ai/deepseek-v4.1-flash",
        "messages": messages,
        "max_tokens": 8192,
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
        with urllib.request.urlopen(req, timeout=1200) as response:
            res_data = json.loads(response.read().decode())
            content = res_data['choices'][0]['message']['content']
            
            with open(proj['output_file'], 'w', encoding='utf-8') as f:
                f.write(content)
                
            print(f"-> Đã xong {proj['name']}. Số ký tự sinh ra: {len(content)}", flush=True)
    except Exception as e:
        print(f"Lỗi ở dự án {proj['name']}: {e}", flush=True)

print("\\nĐã hoàn thành toàn bộ Pipeline cho 3 dự án!", flush=True)
