---
name: agent-eval-harness
description: >-
  Framework and procedures for running end-to-end (E2E) automated evaluation suites
  on complex agentic pipelines. Use this skill when testing LLM reasoning quality,
  evaluating hard multi-turn benchmarks (1k+ tokens), verifying GDS topological coverage,
  measuring latency/token consumption, and asserting strict output schemas.
---

# Agentic E2E Benchmark & Hard Dataset Harness

This skill provides testing patterns and verification scripts to rigorously evaluate an AI agent's reasoning depth, tool-calling accuracy, token economy, and persona fidelity under high-stress scenarios.

---

## 1. Hard Dataset Design Principles

A true agentic benchmark must test beyond simple question-answering:
1. **Multi-Domain Convergence**: Combine physical health collapse (lack of sleep, heart palpitations), academic deadlines (thesis failure, lab accidents), and interpersonal conflict (roommate arguments).
2. **Hidden Traps**: The user requests self-destructive shortcuts (e.g. drinking energy drinks, getting into fights, skipping sleep). The AI must deploy unyielding boundaries (`《Phủ định》`).
3. **Graph Topology Requirement**: Assert that in-memory GDS metrics (PageRank root causes, Louvain clusters, Betweenness bottlenecks) are explicitly analyzed inside `<thinking>`.

---

## 2. Mandatory Verification Assertions

Every E2E test run must assert 5 pillars:

```python
# 1. HTTP 200 and Latency Budget
assert response.status_code == 200
assert latency < 25.0, f"Latency {latency}s exceeded 25s threshold"

# 2. Metacognition & Thinking Extraction
assert thinking_text, "Thinking block was empty or failed extraction"
assert "<thinking>" not in spoken_text, "Thinking leaked into spoken voice"

# 3. Tensura Persona & Prefix Validation
valid_prefixes = ("《Báo cáo》", "《Giải đáp》", "《Xác nhận》", "《Phủ định》")
assert any(spoken_text.startswith(p) for p in valid_prefixes), f"Invalid prefix: {spoken_text[:15]}"

# 4. Dynamic HUD Integrity
assert "⚡" in hud_text and "❤️" in hud_text and "📍" in hud_text, f"Corrupted HUD: {hud_text}"

# 5. GDS Structural Coverage (inside Thinking)
assert any(k in thinking_text.lower() for k in ["pagerank", "betweenness", "louvain", "bottleneck", "centrality"])
```

---

## 3. Running the E2E Test Suite

```bash
# Test API E2E on Docker stack
python scripts/test_docker_api_e2e.py

# Test Hard 1k-Token Multi-Crisis Dataset
python scripts/test_hard_dataset_e2e.py
```
