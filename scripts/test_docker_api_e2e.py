# -*- coding: utf-8 -*-
"""
scripts/test_docker_api_e2e.py — End-to-End Test for Running Docker API Container
Sends HTTP requests to http://localhost:8000/api/chat, testing:
- Container-to-Container connectivity: API container -> Neo4j container (with GDS)
- DeepSeek reasoning loop inside the container
- GDS context synthesis & response format
"""

import sys
import requests
import json
import time

sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000"

def test_docker_stack():
    print("=" * 80)
    print("🐳 DOCKER STACK END-TO-END VERIFICATION: API + BOT + NEO4J GDS")
    print("=" * 80)

    # 1. Health check
    print("\n1. Testing GET /health ...")
    r = requests.get(f"{API_URL}/health")
    print(f"Status: {r.status_code}, Response: {r.json()}")
    assert r.status_code == 200

    # 2. Desktop Adapter Chat Health
    print("\n2. Testing GET /api/chat ...")
    r = requests.get(f"{API_URL}/api/chat")
    print(f"Status: {r.status_code}, Response: {r.json()}")
    assert r.status_code == 200

    # 3. Post Chat Prompt to trigger Core Brain + GDS inside Docker container
    print("\n3. Testing POST /api/chat (End-to-End Brain + GDS + DeepSeek via Docker) ...")
    payload = {
        "prompt": "Hôm nay lại bị cháy board STM32 khi nạp firmware, áp lực đồ án với thầy Hùng quá...",
        "user_id": "8763843475",
        "stream": False
    }
    
    t0 = time.perf_counter()
    r = requests.post(f"{API_URL}/api/chat", json=payload, timeout=180)
    latency = (time.perf_counter() - t0) * 1000

    print(f"Status: {r.status_code}, Latency: {latency:.1f}ms")
    assert r.status_code == 200

    data = r.json()
    print("\n[RESPONSE DATA FROM DOCKER API]:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    print("\n" + "=" * 80)
    print("✓ DOCKER END-TO-END VERIFICATION SUCCESSFUL!")
    print("=" * 80)

if __name__ == "__main__":
    test_docker_stack()
