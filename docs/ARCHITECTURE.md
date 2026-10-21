# ARCHITECTURE — Raphael Life OS (Amazing Nobel)

> System facts only. Process rules live in [AGENTS.md](../AGENTS.md).
> **Sync rule (AGENTS.md Rule 6):** any merge that changes modules, data stores, model/endpoint config, or runtime flow must update this file in the same PR.

Last verified: 2026-10-21 · code graph rebuilt at `b35b053` (1,244 nodes / 1,983 edges); no runtime component was removed since — only the `docs/tien_kiep/` history archive, its eight generator scripts, `.archify/` and the unregistered `mcp_server.py`.

## 1. Topology

```text
                                 [ MASTER / USER ]
              (Input: Text, Photos, Audio, Live Location H3 Resolution 9)
==========================================================================================
          | (Data Stream)                                                    ^ (Execution)
          v                                                                  |
+----------------------------------------------------------------------------------------+
| TELEGRAM ADAPTER (bot/main.py & bot/handlers/)                                         |
| - Detects commands, messages, images.                                                  |
| - Background trigger: H3 (hex) coords -> compare old/new cell -> fire background task.  |
+----------------------------------------------------------------------------------------+
          |
          v
+----------------------------------------------------------------------------------------+
| CORE BRAIN (core/brain.py) — ORCHESTRATOR                                               |
| [ OMNI-AGENTIC LOOP ] DeepSeek (official API first, SiliconFlow fallback)               |
| - Loops reading context; emits tool calls when data is missing                          |
|            `search_memory_and_causality()`                                              |
+----------------------------------------------------------------------------------------+
          | (Tool Calling)
          +------------------------+-------------------------+------------------------+
          v                        v                         v
+----------------------+  +----------------------+  +----------------------+
| SQLITE               |  | NEO4J (causal graph) |  | MEM0 (vector)        |
| Users & MessageLogs  |  | Causal nodes         |  | Qwen3-Embedding-8B   |
| FTS5 sparse search   |  | H3 grid cells        |  | (4096 dims)          |
| (exact keywords)     |  | [:VISITED] relations |  | semantic storage     |
+----------------------+  +----------------------+  +----------------------+
          | Top 5 chunks            | graph paths              | Top 5 chunks
          +-------------------------+--------------------------+
                                    v
+----------------------------------------------------------------------------------------+
| RERANKER — Qwen3-Reranker-8B (SiliconFlow /v1/rerank)                                  |
| Scores + compresses context, returns it to the model as a tool result.                 |
+----------------------------------------------------------------------------------------+
                                    v
+----------------------------------------------------------------------------------------+
| PASS 2 — DeepSeek reasoning + persona synthesis                                        |
| [HIDDEN <thinking>] causal impact -> psychology -> intent delta -> synthesis           |
| [METACOGNITION]     thinking block persisted back as an event on the Master's input    |
+----------------------------------------------------------------------------------------+
                +-------------------+---------------------------+
                v                                               v
+---------------------------------+   +----------------------------------------------------+
| RAPHAEL'S VOICE (output)        |   | BACKGROUND TRIGGERS (side quests)                  |
| Concise, HUD attached           |   | H3 cell transition, energy/mood drop               |
| push toward ideal state         |   | writes SystemQuest + penalty, pushes Telegram       |
+---------------------------------+   +----------------------------------------------------+
```

## 2. Components

| Component | Path | Role |
|---|---|---|
| Telegram adapter | `bot/main.py`, `bot/handlers/` | ingress, documents, location, quests, reset, onboarding |
| Core brain | `core/brain.py` | orchestrator loop, pass 2, async state writes |
| LLM layer | `core/llm.py`, `core/llm_tools.py` | prompts, tool schemas, dispatch |
| Memory | `core/memory.py`, `core/omniscience.py` | Mem0 + pre-fetch context |
| Graph | `core/neo4j_client.py`, `core/gds_service.py` | causal graph, GDS projections |
| Spatial | `core/spatial.py`, `bot/handlers/location.py` | H3 resolution 9 tracking |
| Output contract | `core/hud.py` | HUD line formatting |
| Scheduler | `core/scheduler.py` | reminders, daily check-in |
| API | `api/main.py`, `api/routes/desktop.py` | FastAPI, desktop SSE stream |
| DB | `db/models.py`, `db/database.py` | SQLModel tables, FTS5 triggers |

## 3. Tri-store memory

| Store | Holds | Retrieval |
|---|---|---|
| SQLite + FTS5 | users, message logs, quests, life states, ambient transcripts | exact-keyword sparse search, top 5 |
| Mem0 / ChromaDB | semantic facts and preferences, 4096-dim Qwen3 embeddings | vector top 5, fact decay on overwrite |
| Neo4j 5.12 + APOC + GDS | causal nodes, psychology edges, H3 cells | graph paths, GDS triage |

## 4. Causal graph schema (mandatory on every Neo4j write)

- **Physical layer:** `Person`, `Location`, `Object`, `LifeEvent`
- **Cognitive layer:** `Emotion`, `DefenseMechanism`, `CoreBelief`
- **Edges:** `TRIGGERS`, `CAUSES`, `REINFORCES`, `MITIGATES`, `LOCATED_IN`, `RELATED_TO`
- Always `MERGE`, never `CREATE` — duplicate nodes poison GDS projections.

## 5. Model & endpoints

| Setting | Env var | Default / behavior |
|---|---|---|
| Primary API | `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` (official) |
| Fallback | `SILICONFLOW_API_KEY` | `https://api.siliconflow.com/v1` — **`.com`, never `.cn`** |
| Model | `DEEPSEEK_MODEL` | `deepseek-flash`; falls back to `deepseek-ai/deepseek-v4.1-flash` on SiliconFlow |
| Reasoning | `DEEPSEEK_REASONING_EFFORT` | `low` (accepts `high`, or `none`/`off` to disable) — passed as a request body field, not a dotted path |
| Token caps | `DEEPSEEK_MAX_TOKENS`, `DEEPSEEK_ORCHESTRATOR_MAX_TOKENS` | 1500 / 1024 |
| Embeddings | Mem0 config | Qwen3-Embedding-8B, 4096-d |
| Reranker | `RERANKER_API_URL` | `https://api.siliconflow.com/v1/rerank` |

## 6. Output & interaction contract

- **HUD**, rendered by `core/hud.py`: `⚡ {energy}/10 | 😐 {mood}/10 | ❤️ {health}/10 | 💎 {credits}cr | 📍 H3:{hex}`.
- **Spoken output:** calm mentor tone, HHH, 1–2 sentences, Vietnamese (or the Master's language).
- **Hidden reasoning:** every deep analysis stays inside `<thinking>`; nothing from it is spoken — "insight given is insight rejected".
- **Routing:** NLP only — no `ConversationHandler`, no hard-coded menus.
- **Code conventions:** `async/await` throughout, type hints mandatory; write UTF-8 through Python, not shell here-strings.

## 7. Known gaps

- The `SCORER & FILTER` box in the diagram has no single module — reranking is spread across `core/memory.py` and tool handlers.
- Metacognition persistence is described as writing to three stores; only graph persistence is confirmed in code.
- `GDSService`, `core/scheduler.py` and `api/routes/desktop.py` carry recent design work but are not yet reflected in `docs/ENGINEERING_NOTEBOOK.md`.
