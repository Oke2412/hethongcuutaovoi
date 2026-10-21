# SKILLS & MCP — routing table

> Read once when a task starts, never every turn. Load **one** skill whose trigger matches; a second only when the work truly spans two domains.

## Skills (8)

| Skill | Trigger |
|---|---|
| `deepseek-token-budgeter` | **Always on** — reasoning effort, token caps, BPE economy |
| `graphify` | Structure / call-flow / "where is X"; with `graphify-out/graph.json` use `mcp__graphify__*` before re-reading files |
| `web-search` | External facts for AGENTS.md Rule 4: API and model docs, versions |
| `agent-eval-harness` | Running or extending `scripts/evaluate_pipeline_harness.py`, `scripts/test_hard_dataset_e2e.py` |
| `database-migration-alembic` | `db/models.py`, `migrate_sqlite.py`, FTS5 triggers, schema migration |
| `docker-homelab-devops` | `docker-compose.yml`, healthchecks, live reload, container networking |
| `fastapi-sse-streaming` | `api/routes/desktop.py`, SSE frames, token streaming, disconnect handling |
| `neo4j-gds-expert` | `core/gds_service.py`, `core/neo4j_client.py`; projections, PageRank/Louvain/paths |

All eight live in `.dsh/skills/<name>/SKILL.md`; `graphify` is global (`~/.agents/skills/graphify/`). If this table and the harness catalog disagree, the catalog wins.

## MCP servers (1)

| Server | Status |
|---|---|
| `graphify` | registered as `mcp-graphify` in `~/.dsh/profiles/<profile>/cordis.patch.yml` — stdio, `~/.local/bin/graphify-mcp <repo>/graphify-out/graph.json`, 60 s timeout. Tools: `query_graph`, `get_node`, `get_neighbors`, `get_community`, `god_nodes`, `graph_stats`, `shortest_path`, `list_prs`, `get_pr_impact`, `triage_prs` |

Nothing else is registered. The old `raphael-fs` server (`mcp_server.py`) was removed — the harness filesystem tools replaced it.

## Keeping the graph usable

```bash
graphify update .          # re-extract changed files, no LLM, refreshes graph.json
graphify query "..."       # BFS over the graph
graphify path "A" "B"      # shortest path between two nodes
```

`graph.json` is gitignored — a rebuildable artifact. Rebuild after cloning or after merging work that touches `core/`, `api/`, `db/`, `bot/`, or this catalog, otherwise the MCP answers describe an older tree.

Schema, stores and runtime config: [ARCHITECTURE.md](ARCHITECTURE.md).
