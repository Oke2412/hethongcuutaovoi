import urllib.request
import json
import os
import sys
from urllib.error import HTTPError
from dotenv import load_dotenv

load_dotenv('C:/Users/Asus/Documents/antigravity/amazing-nobel/.env')
api_key = os.environ.get('SILICONFLOW_API_KEY').strip('"\'')

with open('C:/Users/Asus/Documents/antigravity/amazing-nobel/docs/tien_kiep/pure_full_history.txt', 'r', encoding='utf-8') as f:
    history_text = f.read()
    
messages = [
    {'role': 'system', 'content': 'Test'},
    {'role': 'user', 'content': history_text[:3500000]}
]
    
req_data = {
    'model': 'deepseek-ai/deepseek-v4.1-flash',
    'messages': messages,
    'max_tokens': 100,
    'temperature': 0.25,
    'stream': False
}

req = urllib.request.Request(
    'https://api.siliconflow.com/v1/chat/completions',
    data=json.dumps(req_data).encode('utf-8'),
    headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
)

try:
    print('Gửi request test...')
    with urllib.request.urlopen(req, timeout=120) as response:
        print('Thành công!', response.read().decode())
except HTTPError as e:
    print(f'HTTP Error: {e.code}')
    print(f'Raw Body: {e.read().decode()}')
except Exception as e:
    print(f'Lỗi khác: {e}')
