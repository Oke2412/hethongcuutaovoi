# -*- coding: utf-8 -*-
"""scripts/probe_sse_stream.py — Live timeline probe for the SSE chat transport.

Measures what the user actually feels:
  T0  → first byte received          (should be ≈0, proves the stream opens at once)
  T0  → first heartbeat              (proves the socket stays alive while thinking)
  T0  → first spoken token           (the real perceptual latency)
  T0  → final event                  (end-to-end, HUD + metacognition delivered)

Requires the API to be up (`docker compose up -d`). Usage:

    python scripts/probe_sse_stream.py
    python scripts/probe_sse_stream.py --url http://127.0.0.1:8000/api/chat
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from typing import Any, Dict, List

import httpx

PROMPT = (
    "48 tiếng nữa bảo vệ đồ án, mạch STM32 cháy, thầy Hùng dọa hoãn tốt nghiệp, "
    "tôi thức 38 tiếng rồi và đang rất hoảng. Tôi nên làm gì ngay bây giờ?"
)


async def probe(url: str, prompt: str) -> int:
    timeline: List[tuple[float, Dict[str, Any]]] = []
    spoken = ""

    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            url,
            json={"prompt": prompt, "stream": True, "user_id": "8763843475"},
            headers={"Accept": "text/event-stream"},
        ) as response:
            response.raise_for_status()
            async for raw in response.aiter_lines():
                if not raw.startswith("data: "):
                    continue
                body = raw[6:]
                if body.strip() == "[DONE]":
                    break
                try:
                    payload = json.loads(body)
                except json.JSONDecodeError:
                    continue
                timeline.append((time.perf_counter() - started, payload))
                if payload.get("type") == "token":
                    spoken += payload.get("text", "")

    total_ms = (time.perf_counter() - started) * 1000

    def first(pred) -> float:
        for at, payload in timeline:
            if pred(payload):
                return at
        return float("nan")

    first_byte_ms = timeline[0][0] * 1000 if timeline else float("nan")
    first_beat_ms = first(lambda p: p.get("type") == "heartbeat") * 1000
    first_token_ms = first(lambda p: p.get("type") == "token") * 1000
    final_ms = first(lambda p: p.get("type") == "final") * 1000

    print("=" * 74)
    print("SSE TIMELINE")
    print("=" * 74)
    print(f"  first byte          {first_byte_ms:>9.0f} ms")
    print(f"  first heartbeat     {first_beat_ms:>9.0f} ms")
    print(f"  first spoken token  {first_token_ms:>9.0f} ms   <- perceived latency")
    print(f"  final event         {final_ms:>9.0f} ms")
    print(f"  [DONE] / total      {total_ms:>9.0f} ms")
    print("-" * 74)

    counts: Dict[str, int] = {}
    for _, payload in timeline:
        counts[payload.get("type", "?")] = counts.get(payload.get("type", "?"), 0) + 1
    print("  events:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))

    phases = [p.get("phase") for _, p in timeline if p.get("type") == "phase"]
    print("  phases:", " → ".join(phases))
    print("  spoken:", spoken.strip()[:160] or "(none)")

    leaked = [p for _, p in timeline if "Suy luận" in str(p.get("text", ""))]
    print("  reasoning leak:", "YES" if leaked else "no")

    ok = first_byte_ms < 500 and not leaked and spoken.strip()
    print("=" * 74)
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000/api/chat")
    parser.add_argument("--prompt", default=PROMPT)
    args = parser.parse_args()
    return asyncio.run(probe(args.url, args.prompt))


if __name__ == "__main__":
    raise SystemExit(main())
