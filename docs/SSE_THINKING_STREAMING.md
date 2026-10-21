# SSE during thinking — continuous experience design

**Scope:** remove loop 3 from the critical path + make the transport stream while the model reasons.
**Branch:** `feature/defer-writes-and-sse-thinking`
**Related:** [latency breakdown](./LATENCY_BREAKDOWN_22S.md) · [SSE skill](../.dsh/skills/fastapi-sse-streaming/SKILL.md)

---

## 1. The two defects

**Defect A — a state-write turn sat in front of the answer.**
`task-3520` measured loop 3 at **4,774.6 ms**. That turn is *thinking* — deciding what to record about Master (energy, quests, credits) is part of reasoning in a psychological system, so it stays. What must not stay is its *tool execution* blocking Pass 2: those tools run in **0.1 ms** and return **6 tokens** each. The fix is therefore **"think inline, execute concurrently"**, not "delete the turn".

> ⚠️ Scope note: an earlier revision of this branch removed the write turn from the orchestrator entirely. That was reverted — it removed the reasoning step the system depends on. The write *decision* is now back inside the loop; only the *execution* moved.

**Defect B — the "streaming" endpoint did not stream.**
`api/routes/desktop.py` awaited the entire `brain.process_input()` (~20 s), then replayed the finished sentence word by word with `await asyncio.sleep(0.02)`. The socket was silent for the whole thinking phase; the client saw first byte at T+20 s. It was a typewriter on a finished document, not a stream.

---

## 2. How DeepSeek streams reasoning

Per the [DeepSeek streaming thinking sample](https://api-docs.deepseek.com/api_samples/thinking_mode_api_example_streaming/), a reasoning-enabled completion with `stream=True` emits deltas in two consecutive phases:

```python
for chunk in response:
    if chunk.choices[0].delta.reasoning_content:
        reasoning_content += chunk.choices[0].delta.reasoning_content   # phase 1: thinking
    else:
        content += chunk.choices[0].delta.content                       # phase 2: answer
```

So a single request already carries the information needed to keep a UI alive: **reasoning arrives first, answer second**. Nothing in the API forces silence.

The constraint is product-side, not transport-side: rule 4 of `AGENTS.md` — *"Insight given is insight rejected"* — forbids showing chain-of-thought. Therefore reasoning is **counted and timed, never forwarded**.

| Channel | Content | Sent to client |
|---|---|---|
| `phase` | pipeline stage label (`ingress` → `recall` → `reasoning`) | yes |
| `loop` | orchestrator loop index, decide time, tool-call count | yes |
| `tool` | tool name, execution ms, `done` / `async` | yes |
| `reasoning` | **token count only** (no text), every 250 ms | yes |
| `token` | answer deltas, verbatim | yes |
| `heartbeat` | keep-alive every 1 s of silence | yes |
| thinking text | raw chain-of-thought | **never** (delivered once, in `final.thinking`, for metacognition) |

---

## 3. What changed in code

### 3.1 Tool classification — `core/llm.py`

```python
WRITE_TOOLS = {"ingest_knowledge", "cancel_quest", "complete_quest", "create_quest",
               "manage_user_status", "update_physical_status", "manage_project",
               "manage_capability", "manage_credits"}      # 9 of the 12 tools

# TOOLS_DEF is unchanged and still offered in full — the orchestrator decides.
```

This set is a **classifier, not a filter**. Every tool stays on the table; the brain only needs to answer one question per turn: *did this turn ask for nothing but writes?* That question decides scheduling, not capability.

### 3.2 Concurrent write execution — `core/brain.py`

After each orchestrator turn:

```python
write_only = all(tc.function.name in WRITE_TOOLS for tc in msg.tool_calls)
if write_only and settings.deepseek_defer_writes:
    for tc in msg.tool_calls:
        task = asyncio.create_task(_apply_write(tc.function.name, args, user_id))  # not awaited
    break                      # → Pass 2 starts now; the writes land during it
# mixed read+write turn → executed inline and answered back to the model, as before
```

- The model **still thinks** the write turn (decides the values, the quest text, the ingest payload).
- The **tools execute concurrently with Pass 2** and their (information-free) confirmation never delays the answer.
- `DEEPSEEK_DEFER_WRITES=false` restores the byte-for-byte original pipeline — write executed inline, loop continues to `TERMINATE_LOOP`. Both paths are covered by tests.

**Honest accounting.** This saves the *execution* (0.1 ms), not the *decision* (4,774.6 ms — that is model latency on a 3.5 k-token context). It is the correct change for correctness-under-latency, but it is **not** the 4.7 s the earlier report promised. See §9 for the only two ways to actually reclaim that time.

### 3.3 Live events — `core/brain.py`

`process_input(..., on_event=callable)` — an optional async sink. When present, Pass 2 uses `stream=True` and forwards `content` deltas as `token` events while counting `reasoning_content`. When absent (Telegram bot), the code path is byte-for-byte the old one.

### 3.4 Real SSE — `api/routes/desktop.py`

The endpoint now returns `StreamingResponse` **before** the turn starts: the generator drains an `asyncio.Queue` fed by `on_event`, injecting `heartbeat` frames during silence. Client disconnect stops streaming but **does not cancel the turn** — state writes and metacognition logging must still land.

---

## 4. Event contract

```text
data: {"type":"open","elapsed_ms":0}
data: {"type":"phase","phase":"ingress","label":"Nhận tri giác","elapsed_ms":3}
data: {"type":"phase","phase":"recall","label":"Truy xuất ký ức","elapsed_ms":4}
data: {"type":"loop","index":1,"status":"start","elapsed_ms":5}
data: {"type":"loop","index":1,"status":"decided","decide_ms":2939,"tool_calls":3,"elapsed_ms":2951}
data: {"type":"tool","name":"search_memory_and_causality","status":"done","ms":2816,"elapsed_ms":5770}
data: {"type":"heartbeat","elapsed_ms":6770}
data: {"type":"phase","phase":"reasoning","label":"Suy luận nhân quả","elapsed_ms":11800}
data: {"type":"reasoning","tokens":312,"elapsed_ms":14100}
data: {"type":"token","text":"《Phủ định》 ","token":"《Phủ định》 ","response":"《Phủ định》 "}
data: {"type":"final","text":"...","thinking":"...","hud":"━━━ ...","has_keyboard":false,"elapsed_ms":17200}
data: [DONE]
```

`token` frames keep the legacy keys (`text` / `token` / `response`) so the existing Tauri client renders them unchanged; everything else is additive, and clients that ignore unknown `type`s degrade to the old behaviour.

---

## 5. Client contract (Tauri / web)

```javascript
if (evt.type === "token")     appendText(evt.text);          // speak immediately
else if (evt.type === "phase") setStage(evt.phase);          // "đang truy xuất ký ức…"
else if (evt.type === "reasoning") bumpThinkingMeter(evt.tokens);  // no text, no CoT
else if (evt.type === "heartbeat") keepSpinnerAlive(evt.elapsed_ms);
else if (evt.type === "final") { showHud(evt.hud); logThinking(evt.thinking); }
```

Rules for the frontend:

1. **Paint on `open`, not on the first token** — the socket opens in < 100 ms.
2. **Never render `reasoning.tokens` as text** — it is a counter, not a payload.
3. **Start TTS on the first `token`** — the 20 ms replay delay is gone; the deltas are the real cadence.
4. Treat 1 s of silence as normal, 5 s as degraded, 30 s as dead (heartbeat is proof of life).

---

## 6. Expected effect

| Metric | Before | After |
|---|---:|---:|
| First byte | ≈20,290 ms (after the whole turn) | **< 100 ms** |
| Heartbeat during thinking | none | every **1,000 ms** |
| Write execution in front of the answer | 0.1 ms (but 4,774.6 ms of decision) | **0 ms** (concurrent with Pass 2) |
| Write decision on the critical path | 4,774.6 ms | **4,774.6 ms** (deliberately kept) |
| Coin-flip: is the socket alive? | unknown for 20 s | always known |

The reasoning phase still takes its ~8 s on a single-request answer — that is a *model* cost, not a transport cost; §9 is what shortens it. What changes here is that those 8 s are **visible** instead of **dead**.

---

## 7. Verification

```powershell
# offline: classification, async dispatch, sequential fallback, frame order
# — no Docker, no network
python tests/test_stream_pipeline.py
#   PASS — 3 read tools, 9 write tools, all defined
#   PASS — write turn kept, dispatched async, scribe-free, 2 token frames
#   PASS — sequential mode: write executed inline, loop continued to terminate
#   PASS — SSE frames: open → heartbeat → token → final → [DONE]

# live: perceptual timeline against the running API
docker compose up -d
python scripts/probe_sse_stream.py
```

`probe_sse_stream.py` reports first byte, first heartbeat, first spoken token and final, and fails if any reasoning text leaks into a `token` frame.

---

## 8. Known limits / follow-ups

1. **First spoken token still waits for the reasoning phase to end.** The answer is one completion; DeepSeek emits `content` only after thinking. A true "one syllable immediately" experience needs either a speculative acknowledgement event (`⚠ P0 detected, đang soạn`) or a two-stage answer — not done here.
2. **`THINKING_BUDGET: 100–150 words` is still an instruction, not a constraint.** Measured 1,218 reasoning tokens vs a ~200-token target. Capping it is the single largest remaining win (~6 s) and was explicitly out of scope.
3. **Ordering.** A dispatched write lands a few hundred ms *after* the answer starts streaming. If the answer quotes the new state (e.g. a quest ID), it quotes an intention, not a persisted row.
4. **Concurrency surface.** A background `_apply_write` and Pass 2 overlap. Pass 2 writes nothing to SQLite until after it returns (log/mem0/graph run in their own background tasks), so there is no write-write race today — but any future tool that both writes and influences the answer would break this assumption.

---

## 9. The only two ways to actually reclaim the 4.7 s

The write turn is 4,774.6 ms of **model time**, so moving its execution cannot remove it. Real options:

| Option | Mechanism | Saves | Cost / risk |
|---|---|---:|---|
| **A. Overlap the write *thinking* with Pass 2** | after the last read turn, run the write-turn LLM call with `WRITE_TOOL_DEFS` in parallel with persona synthesis; both share the same input snapshot | ~4.7 s | two concurrent model calls; write turn can no longer ask for another read **or** contribute `<tool_data>` to `sensor_truth`; needs a discard path if it fails |
| **B. Cap Pass 2 reasoning** | enforce the 150-word thinking budget | ~6.0 s | shortens the deepest psychological triage — a product decision, not a technical one |
| A + B | — | **~10.7 s** (20.3 s → ~9.6 s) | — |

Both are deliberately **not** implemented on this branch: each changes either what the model may reason about or how deep it reasons, and that is the user's call, not a latency optimisation.

