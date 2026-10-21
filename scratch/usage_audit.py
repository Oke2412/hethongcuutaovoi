# -*- coding: utf-8 -*-
"""Sum token usage recorded in DSH session logs."""

from __future__ import annotations

import glob
import json
import os
from collections import defaultdict

ROOT = os.path.expanduser(r"~\.dsh\sessions")


def walk(obj, found):
    """Collect usage-ish dicts anywhere in an event."""
    if isinstance(obj, dict):
        keys = set(obj)
        if {"inputTokens", "outputTokens"} & keys or {"input_tokens", "output_tokens"} & keys:
            found.append(obj)
        for v in obj.values():
            walk(v, found)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, found)


def num(d, *names):
    for n in names:
        v = d.get(n)
        if isinstance(v, (int, float)):
            return int(v)
    return 0


totals = defaultdict(lambda: {"in": 0, "out": 0, "cached": 0, "req": 0})
for path in glob.glob(os.path.join(ROOT, "**", "*.jsonl"), recursive=True):
    sid = os.path.basename(path)[:20]
    found = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or "usage" not in line and "Tokens" not in line and "tokens" not in line:
                continue
            try:
                walk(json.loads(line), found)
            except json.JSONDecodeError:
                continue
    seen = set()
    for d in found:
        key = json.dumps(d, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        t = totals[sid]
        t["in"] += num(d, "inputTokens", "input_tokens", "prompt_tokens")
        t["out"] += num(d, "outputTokens", "output_tokens", "completion_tokens")
        t["cached"] += num(d, "cachedInputTokens", "cached_tokens", "cache_read_input_tokens")
        t["req"] += 1

grand = {"in": 0, "out": 0, "cached": 0, "req": 0}
for sid, t in sorted(totals.items(), key=lambda kv: -(kv[1]["in"] + kv[1]["out"])):
    if t["in"] + t["out"] == 0:
        continue
    print(f"{sid:22} in={t['in']:>12,}  cached={t['cached']:>12,}  out={t['out']:>9,}  reqs={t['req']}")
    for k in grand:
        grand[k] += t[k]
print("-" * 92)
print(f"{'TOTAL':22} in={grand['in']:>12,}  cached={grand['cached']:>12,}  out={grand['out']:>9,}  reqs={grand['req']}")
print(f"{'TOTAL incl. cache':22} {grand['in'] + grand['out']:,}")
