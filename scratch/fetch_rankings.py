import urllib.request, json

key = 'Bearer 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'
endpoints = [
    'https://openrouter.ai/api/v1/models',
    'https://openrouter.ai/api/v1/rankings',
    'https://openrouter.ai/api/v1/benchmarks',
    'https://openrouter.ai/api/v1/leaderboard'
]

for ep in endpoints:
    req = urllib.request.Request(ep, headers={'Authorization': key})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"SUCCESS: {ep}")
            keys = list(data.keys())
            print(f"  Keys: {keys}")
            if 'data' in data and len(data['data']) > 0:
                print(f"  Sample item keys: {list(data['data'][0].keys())}")
                item = data['data'][0]
                name = item.get('id') or item.get('model_permaslug') or item.get('name')
                print(f"  Sample model: {name}")
    except urllib.error.HTTPError as e:
        print(f"FAILED: {ep} - HTTP {e.code}")
    except Exception as e:
        print(f"FAILED: {ep} - {e}")
