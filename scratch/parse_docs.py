import urllib.request, re, sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

req = urllib.request.Request('https://openrouter.ai/docs/cookbook/administration/data-api', headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Let's find all code blocks or pre tags for exact endpoint URLs
        blocks = soup.find_all(['code', 'pre'])
        print("--- CODE BLOCKS ---")
        for b in blocks:
            text = b.get_text().strip()
            if 'http' in text or 'api/v1' in text or 'curl' in text.lower():
                print(text)
                
except Exception as e:
    print('Error:', e)
