import urllib.request, json
req = urllib.request.Request('https://openrouter.ai/api/v1/benchmarks', headers={'Authorization': 'Bearer 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'})
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        models = data.get('data', [])
        models.sort(key=lambda x: x.get('agentic_index', 0) or 0, reverse=True)
        deepseek = [m for m in models if 'deepseek' in m.get('model_permaslug', '').lower()]
        for m in deepseek:
            print(f"DeepSeek: {m.get('model_permaslug')} | Agentic: {m.get('agentic_index')} | Code: {m.get('coding_index')} | Price: {m.get('pricing')}")
        
        print("\nTop 20 Agentic Models:")
        for idx, m in enumerate(models[:20]):
            print(f"#{idx+1}: {m.get('model_permaslug')} - {m.get('agentic_index')}")
except Exception as e:
    print('Error:', e)
