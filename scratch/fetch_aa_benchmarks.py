import urllib.request, json

key = 'Bearer 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'
url = 'https://openrouter.ai/api/v1/benchmarks?source=artificial-analysis'
req = urllib.request.Request(url, headers={'Authorization': key})

try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        models = data.get('data', [])
        
        deepseek = [m for m in models if 'deepseek' in m.get('model_permaslug', '').lower()]
        
        print("--- DEEPSEEK MODELS (Artificial Analysis) ---")
        for m in deepseek:
            name = m.get('model_permaslug')
            intel = m.get('intelligence_index')
            code = m.get('coding_index')
            agent = m.get('agentic_index')
            price = m.get('pricing', {})
            print(f"[{name}]")
            print(f"  Intelligence: {intel}")
            print(f"  Coding:       {code}")
            print(f"  Agentic:      {agent}")
            print(f"  Pricing:      {price}")
            print("-" * 40)
            
        print("\n--- TOP 20 AGENTIC ---")
        agent_sorted = sorted([m for m in models if m.get('agentic_index') is not None], key=lambda x: x.get('agentic_index', 0), reverse=True)
        for i, m in enumerate(agent_sorted[:20]): 
            print(f"#{i+1} {m.get('model_permaslug')} (Agentic: {m.get('agentic_index')})")
            
except Exception as e:
    print('Error:', e)
