# Latency Breakdown — 22.67s E2E (Raphael Life OS)

**Status:** reconstructed from the Antigravity deep-dive profiler run that was never summarised to Master.
**Date of measurement:** 2026-10-20 · **Report rebuilt:** 2026-10-20 17:45 (+07)
**Model:** `deepseek-ai/deepseek-v4.1-flash` via SiliconFlow · Pass 1 `thinking=disabled`, Pass 2 reasoning enabled
**Infra:** Windows 11 · Docker Compose (`neo4j:5.12` + GDS 2.6.9 + `api` FastAPI + `bot`) · Neo4j bolt `127.0.0.1:7687`

**Evidence (raw, unedited):**

| Source | Path |
|---|---|
| Profiler run (Neo4j up, warm) | `~/.gemini/antigravity/brain/938a7972-…/.system_generated/tasks/task-3520.log` |
| Profiler run (Neo4j cold/down) | `…/tasks/task-3482.log` |
| Harness E2E run (22.67s) | `…/tasks/task-3410.log` |
| Profiler source | [`scripts/profile_pipeline_deep_dive.py`](../scripts/profile_pipeline_deep_dive.py) |
| Harness source | [`scripts/evaluate_pipeline_harness.py`](../scripts/evaluate_pipeline_harness.py) |

---

## 1. TL;DR

1. **22.67s is not the pipeline core — it is the HTTP end-to-end.** The identical workload measured in-process is **20.29s**; the **2.37s** difference is the FastAPI/container hop, not inference.
2. **Almost all of it is model time.** LLM calls alone = `2,939.3 + 1,074.7 + 4,774.6 + 8,243.8 = 17,032.4ms` = **83.9%**. Tool execution adds **3,000.2ms (14.8%)**, and **2,816.1ms of that is a single cold GDS call**. Everything else — DB init, mini-context, context assembly, HUD — is **194.6ms (0.96%)**, leaving ~67ms of loop bookkeeping unattributed.
3. **The loop, not the database, is the bug when the system is healthy.** Three *sequential* orchestrator decisions are made before any answer is written. Loop 3 spends **4.77s on an LLM call whose two tools execute in 0.1ms**. (When Neo4j is *down*, the database does dominate — see §7.)
4. **Thinking tokens are the single largest line item.** Pass 2 emitted **1,218 reasoning tokens** — 40.6% of wall clock for text the Master never sees — against a prompt that asked for "max 100–150 words". The budget is an instruction, not a constraint; nothing enforces it.
5. **Correction to the previous report:** the shipped number (~2,082 tokens) was an *estimate*. Measured with `tiktoken cl100k_base`: **3,091 input + 1,274 output = 4,365 tokens** (2.1x higher).

---

## 2. Measurement matrix

| Run | Tool | Path | End-to-end | Neo4j | Notes |
|---|---|---|---|---|---|
| `task-3410` 15:31 | `evaluate_pipeline_harness.py` | HTTP → FastAPI container | **22.67s** | up | the number that was reported |
| `task-3482` 16:39 | profiler | in-process | **141.52s** | cold/down | 38s driver timeouts per tool call |
| `task-3520` 16:41 | profiler | in-process | **20.29s** | up, warm | full waterfall captured here |

Same payload in all three: the 1,124-token multi-crisis dataset (`48h to defense / burned STM32 / 38h no sleep / roommate conflict`).

---

## 3. Waterfall (exact — `task-3520`)

```text
PASS 1 — Orchestrator agentic loop (thinking disabled)     11,786.8ms  58.1%
  ├─ Loop 1  LLM decide                                     2,939.3ms
  │    ├─ tool search_memory_and_causality (COLD)           2,816.1ms   <- GDS projection build
  │    ├─ tool search_memory_and_causality                     71.9ms
  │    └─ tool search_memory_and_causality                     73.9ms
  ├─ Loop 2  LLM decide                                     1,074.7ms
  │    ├─ tool analyze_graph_data_science                      16.5ms
  │    └─ tool analyze_graph_data_science                      19.2ms
  └─ Loop 3  LLM decide                                     4,774.6ms
       ├─ tool ingest_knowledge                                 0.0ms   (stub)
       └─ tool update_physical_status                           0.0ms   (stub)

PASS 2 — Persona synthesis (reasoning enabled)               8,243.8ms  40.6%
  └─ 1,218 reasoning tokens + 56 spoken tokens

INGRESS / EGRESS
  ├─ init_db                                                    11.6ms   0.06%
  ├─ get_mini_context                                          181.0ms   0.89%
  ├─ context assembly + GDS synthesis                            0.1ms   0.00%
  └─ HUD + post-processing                                       1.9ms   0.01%
──────────────────────────────────────────────────────────────────────────
   TOTAL (in-process)                                       20,292.2ms  100.00%
```

| Stage | ms | Share |
|---|---:|---:|
| `01_init_db` | 11.6 | 0.06% |
| `02_get_mini_context` | 181.0 | 0.89% |
| `03_pass1_loop_1` | 5,901.5 | 29.08% |
| `03_pass1_loop_2` | 1,110.6 | 5.47% |
| `03_pass1_loop_3` | 4,774.7 | 23.53% |
| `04_context_assembly_and_gds` | 0.1 | 0.00% |
| `05_pass2_synthesis` | 8,243.8 | 40.63% |
| `06_hud_and_postprocessing` | 1.9 | 0.01% |
| **TOTAL** | **20,292.2** | **100%** |

### Per-loop accounting

| Loop | LLM decide | Tool exec | Loop total | Tools issued | Outcome |
|---|---:|---:|---:|---|---|
| 1 | 2,939.3 | 2,962.1 | 5,901.5 | 3 × `search_memory_and_causality` | first call cold: 2.8s, next two 72ms |
| 2 | 1,074.7 | 36.0 | 1,110.6 | 2 × `analyze_graph_data_science` | cheap, correct |
| 3 | 4,774.6 | 0.1 | 4,774.7 | `ingest_knowledge`, `update_physical_status` | **pure latency, zero information gained** |

> `ingest_knowledge` / `update_physical_status` are stubbed inside the profiler (`Tool X executed.`, 6 tokens) — so their 0.0ms is an artifact, and the real loop-3 tool cost is *higher* than measured, not lower.

---

## 4. Why 22.67s vs 20.29s — the 2.37s gap

```text
22.666s  harness, over HTTP          (task-3410)
20.292s  profiler, in-process        (task-3520)
───────
 2.374s  non-model overhead, un-instrumented
```

The harness calls `POST http://localhost:8000/api/chat` from the host into the `api` container; the profiler imports the same modules and runs in-process. The delta therefore contains, in unknown proportions:

- Docker userland NAT + TCP handshake per request (no keep-alive reuse of the httpx client between runs)
- JSON serialise/deserialise of the response envelope
- `init_db()` + middleware inside the app process (already counted separately in-process: 11.6ms)
- run-to-run model variance (SiliconFlow queue time is not pinned)

**Do not treat 2.37s as a fixed constant** — it is a single-run subtraction from two different days/warmth states. To make it exact, the API must emit `Server-Timing` headers per stage; that instrumentation does not exist yet.

---

## 5. Token inventory (measured, `tiktoken cl100k_base`)

| Block | Tokens |
|---|---:|
| `SYSTEM_ORCHESTRATOR` (Pass 1) | 447 |
| `SYSTEM_RAPHAEL` (Pass 2) | 1,365 |
| User message (multi-crisis dataset) | 1,124 |
| Mini-context from SQLite | 45 |
| `<sensor_truth>` (GDS + tri-store tool output) | 179 |
| **Pass 2 prompt (assembled)** | **1,726** |
| **Pass 2 total input (system + prompt)** | **3,091** |
| Reasoning tokens (`<thinking>`) | 1,218 |
| Spoken tokens (Tensura voice) | 56 |
| **Total output billed** | **1,274** |

**Delta vs the previously reported numbers:**

| | Reported (estimated) | Measured | Factor |
|---|---:|---:|---|
| Input | ~1,979 | 3,091 | 1.56x |
| Reasoning | ~64 | 1,218 | **19x** |
| Spoken | ~39 | 56 | 1.4x |
| **Total** | **~2,082** | **4,365** | **2.1x** |

Root cause of the 19x reasoning blowup: the Raphael prompt asks for `THINKING_BUDGET: at most 100–150 words`, but nothing enforces it. In the 15:31 run the model happened to comply (54 words); in the 16:41 run it produced ~230 words of chain-of-thought. **Instruction-following is not a budget.**

---

## 6. Cost (rates must be confirmed — not asserted here)

Measured billable volume: **3,091 in + 1,274 out**.

```text
cost_usd = 3,091/1e6 * input_rate + 1,274/1e6 * output_rate
```

| Provider | Input rate | Output rate | Cost / turn | 1,000 turns |
|---|---:|---:|---:|---:|
| SiliconFlow `deepseek-v4.1-flash` | _confirm_ | _confirm_ | _derive_ | _derive_ |
| DeepSeek official | _confirm_ | _confirm_ | _derive_ | _derive_ |

> ⚠️ The earlier report's `$0.000359 / turn` was derived from the **estimated** 2,082 tokens, not from this measured 4,365. Re-derive against the live price sheet on the SiliconFlow console before quoting a VNĐ figure again — see [SiliconFlow pricing](https://www.siliconflow.com/pricing) and [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing).

**Cost lever is the same as the latency lever:** cutting reasoning from 1,218 → 200 tokens removes ~1,018 output tokens *and* ~6s of wall clock in one change.

---

## 7. Failure mode found (more important than the 22.67s)

`task-3482` — same payload, Neo4j not ready:

| Stage | Healthy (3520) | Neo4j down (3482) | Change |
|---|---:|---:|---:|
| tool `search_memory_and_causality` (cold) | 2,816ms | 38,364ms | **13.6x slower** |
| Loop 1 total | 5,901.5ms | 114,732.7ms | **19.4x slower** |
| Loop 2 total | 1,110.6ms | 11,935.9ms | 10.7x slower |
| Loop 3 total | 4,774.7ms | 10,429.6ms | 2.2x slower |
| Pass 2 synthesis | 8,243.8ms | 3,868.5ms | 0.47x (**cheaper** — empty context, shorter thinking) |
| **End-to-end** | **20,292.2ms** | **141,519.3ms** | **7.0x slower** |

Three sequential ~38s driver timeouts. The driver blocks the whole turn instead of failing fast. There is no connection timeout ceiling and no circuit breaker; a stopped container silently converts a 20s turn into a 2.5-minute hang. Note the inversion: the failing run spent **81% of its time in Loop 1 alone**, and Pass 2 actually got *faster* because the unavailable graph produced a near-empty `<sensor_truth>`.

---

## 8. Optimisation plan (ranked by measured gain)

| # | Change | Fixes | Est. saving | Risk |
|---|---|---|---:|---|
| 1 | **Hard-cap Pass 2 reasoning** (`max_tokens` on the reasoning segment, or strip-and-retry above 250 tokens) | 1,218 → ~200 tok | **~6.0s** | medium — may truncate genuinely hard triage |
| 2 | **Kill loop 3** — it exists only to mutate state; run those writes *after* Pass 2, off the critical path | 4.77s | **~4.7s** | low — writes are idempotent `MERGE` |
| 3 | **Pre-warm the GDS projection** at boot (and after ingest) instead of lazily on first query | 2.82s → ~70ms | **~2.7s** | low |
| 4 | **Fail fast on Neo4j** — `connection_timeout≈2s`, `max_retry_time≈3s`, degrade to SQLite-only context | 38s → ~2s per call | **handles §7** | low |
| 5 | **Trim Pass 2 input** — 1,365-token persona prompt + 1,726-token assembled prompt | 3,091 → ~2,000 tok | **~1.0s** | medium — persona fidelity |
| 6 | **Close the HTTP gap** — persistent httpx client / SSE first-token streaming so the UI paints before Pass 2 ends | 2.37s | **~2.4s perceived** | low |

Projected after #1–#3: **20.29s → ~6.9s** in-process; ~9s over HTTP. After #4, worst case stays bounded near 7s instead of 141s.

> Order matters: #1 and #2 are one-line/one-block edits and buy 10.7s together. #4 buys *reliability*, which the 22.67s number disguised.

---

## 9. Reproduce

```powershell
# 1. infra must be up (Neo4j is the whole difference between 20s and 141s)
docker compose up -d

# 2. in-process waterfall (what this report is built from)
python scripts/profile_pipeline_deep_dive.py

# 3. HTTP end-to-end (the 22.67s number)
python scripts/evaluate_pipeline_harness.py
```

---

## 10. Caveats (read before quoting these numbers)

- Single run per condition, no warm-up iterations, no p50/p95. Treat ±10% as noise until a 5-run loop exists.
- `task-3520` ran immediately after a full tri-store wipe: Neo4j held 0 nodes, so GDS results were empty (`no central nodes`). On a populated graph the cold projection (#3) would cost **more**, not less.
- Two of the loop-3 tools are profiler stubs; their true latency is unmeasured.
- `tiktoken cl100k_base` over-counts DeepSeek BPE by a small margin — token counts are ±3%, costs follow the provider's own count.
