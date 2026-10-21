# AGENTS.md — project deltas · Raphael Life OS (Amazing Nobel)

> Start every session here, then read the tail of [PROMPT_HISTORY.md](PROMPT_HISTORY.md).
> The global rules in `~/.dsh/AGENTS.md` (R1–R8) apply as written and are **not** restated here. This file adds only what is specific to this repository — keep it that way, one copy per rule.
> Agents that never load the global file (Antigravity, Claude Code on another host) should read the archived ruleset in git history at `c2cba6c`.

**Repo:** a personal "life OS" AI (Raphael) tracking physical state, progress and capabilities, answering through causal + psychological analysis over tri-store memory. Telegram bot + desktop SSE client on a FastAPI backend.

## Where things live

| Question | File |
|---|---|
| What is the system made of? Topology, stores, graph schema, models, endpoints | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Which skill or MCP server applies to this task? | [docs/SKILLS_AND_MCP.md](docs/SKILLS_AND_MCP.md) |
| What happened in earlier sessions? | [PROMPT_HISTORY.md](PROMPT_HISTORY.md) |

`ARCHITECTURE.md` wins on system facts, the global rules win on process.

## Session log — project schema for R1

Append every compressed entry to the **bottom** of `PROMPT_HISTORY.md`, never to this file, with five fields: `Timestamp & scope` · `Context & objectives` · `Actions & changes` · `Decisions & findings` · `Next steps`.

## Graph refresh — project commands for R6

Every merge that changes code: `graphify update . --force`, then `python scripts/graph_doctor.py` (must print `stale files: 0`). AST only — 0 tokens, ~2 s. Token-cost table: [docs/SKILLS_AND_MCP.md](docs/SKILLS_AND_MCP.md).

## Skills — project catalog for R7

Load exactly one skill whose trigger matches; `deepseek-token-budgeter` is always on. Catalog: [docs/SKILLS_AND_MCP.md](docs/SKILLS_AND_MCP.md).

Causal graph schema (3 layers, `MERGE` only, edge types): [docs/ARCHITECTURE.md §4](docs/ARCHITECTURE.md).
