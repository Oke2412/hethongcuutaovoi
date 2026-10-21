# SKILLS & MCP — routing catalog

> Read this when a task starts, not on every turn. Load **one** skill, the one whose trigger matches; load a second only when the work genuinely spans two domains. Never load the whole catalog.

## Pick a skill

| Skill | Where | Trigger | Inject |
|---|---|---|---|
| `graphify` | global `~/.agents/skills/graphify/` | Any question about structure, call flow, "where is X / what calls Y". With `graphify-out/graph.json` present use `mcp__graphify__query_graph` / `get_node` / `shortest_path` instead of re-reading files | RAG |
| `web-search` | repo | External facts for AGENTS.md Rule 4: API/model docs, versions, leaderboards | tool (`web_search`, `web_fetch`) |
| `deepseek-token-budgeter` | repo | **Always on** — reasoning effort, token caps, BPE economy; governs every response | system prompt |
| `agent-eval-harness` | repo | Running or extending E2E benchmarks (`scripts/evaluate_pipeline_harness.py`, `scripts/test_hard_dataset_e2e.py`) | system prompt |
| `database-migration-alembic` | repo | `db/models.py` changes, `migrate_sqlite.py`, FTS5 triggers, SQLite/PG migration | RAG |
| `docker-homelab-devops` | repo | `docker-compose.yml`, healthchecks, live reload, container networking | RAG |
| `fastapi-sse-streaming` | repo | `api/routes/desktop.py`, SSE frames, token streaming, client disconnect | RAG |
| `neo4j-gds-expert` | repo | `core/gds_service.py`, `core/neo4j_client.py`, `scripts/verify_gds_benchmark.py`; projections, PageRank/Louvain/paths | tool |
| `inverted-mcp-builder` | repo | `mcp_server.py`; stdio MCP servers, path sandbox | RAG |
| `playwright-browser-agent` | repo | Headless UI verification of the desktop/SSE surface | tool |
| `inter-agent-bridge` | repo | Only if `bridge/agent_chat.log` exists — **it does not in this checkout** | system prompt |
| `tauri-v2-dev` | repo | Windows Tauri desktop; `tauri-desktop/` is **not in this repo**, so not applicable on this Linux host | RAG |

Repo-local skills live in `.dsh/skills/<name>/SKILL.md`. The global pool is `~/.agents/skills/`. If this table and the harness catalog disagree, the catalog wins — the file list can drift.

## MCP servers

Registered per profile in `~/.dsh/profiles/<profile>/cordis.patch.yml`. There is no `~/.gemini/` tree on this host; Windows-era paths in old notes are dead.

| Server | Status | Notes |
|---|---|---|
| `graphify` | **registered** as `mcp-graphify` | stdio, `~/.local/bin/graphify-mcp <repo>/graphify-out/graph.json`, 60 s call timeout. Tools: `query_graph`, `get_node`, `get_neighbors`, `get_community`, `god_nodes`, `graph_stats`, `shortest_path`, `list_prs`, `get_pr_impact`, `triage_prs` |
| `raphael-fs` | code only, **not registered** | `mcp_server.py`, single tool `read_local_file`, CWD-locked read-only |
| `fetch` | not registered | would need `uvx mcp-server-fetch` |
| `chrome_devtools` | absent | Antigravity built-in schemas, Windows-only |

## Keeping the graph usable

```bash
graphify update .          # re-extract changed code files, no LLM, refreshes graph.json
graphify query "..."       # BFS over the graph
graphify path "A" "B"      # shortest path between two nodes
graphify explain "X"       # neighbourhood of a node
```

`graph.json` is gitignored on purpose — it is a rebuildable artifact. Rebuild it after cloning the repo or merging work that touches `core/`, `api/`, `db/` or `bot/`, otherwise the MCP answers describe an older tree.

Causal graph schema, stores and runtime config are in [ARCHITECTURE.md](ARCHITECTURE.md).
