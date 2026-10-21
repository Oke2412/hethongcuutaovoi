# AGENTS.md — Agent Rules · Raphael Life OS (Amazing Nobel)

> Read this file and the tail of [PROMPT_HISTORY.md](PROMPT_HISTORY.md) at the start of every session.
> This file holds **process only**. System facts — topology, stores, graph schema, models, endpoints — live in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Never duplicate them here.

**Repo:** a personal "life OS" AI (Raphael) tracking physical state, progress and capabilities, answering through causal + psychological analysis over tri-store memory. Telegram bot + desktop SSE client on a FastAPI backend.

---

## Rule 1 — Compress the session, log it outside this file

1. At the end of a session or milestone, compress what happened into a dense summary; never keep the raw transcript.
2. Do **not** append session logs to this file. Every log goes to [`PROMPT_HISTORY.md`](PROMPT_HISTORY.md), the single session log.
3. Append new entries at the **bottom**, chronological and incremental.
4. Each entry carries: `Timestamp & scope` · `Context & objectives` · `Actions & changes` · `Decisions & findings` · `Next steps`.
5. **100k-token ceiling:** once the live context passes **100k tokens** — or immediately after the harness auto-compacts — compact: write the dense checkpoint to `PROMPT_HISTORY.md` per this rule, drop finished branches of work and stale tool output, then continue from `AGENTS.md` + `docs/ARCHITECTURE.md` + that checkpoint. Never keep working from a truncated transcript.

## Rule 2 — Git branching

1. Never commit or push directly to `main`.
2. Every feature, fix, refactor and experiment gets its own dedicated branch.
3. Use semantic names: `feature/<topic>`, `fix/<topic>`, `docs/<topic>`. `temp`, `test`, `new-branch` are prohibited.
4. `.gitignore` stays authoritative: no `node_modules/`, `venv/`, `__pycache__/`, `.env`, build artifacts or large binaries. Check `git status` before every commit.

## Rule 3 — Report in four pillars

Every task, command run or edit ends with:
**What was done** (actions, files, tools, features) · **How it was done** (method, steps, architecture/algorithm decisions, commands) · **Codebase impact** (files, packages, dirs, env vars, build deps) · **Impact & contribution** (why, operational benefit, side effects, risk).
No superficial summaries — enough depth for immediate review.

## Rule 4 — Research before deciding

No guessing. Before any assessment, answer or design decision:
1. Read the recent sessions in `PROMPT_HISTORY.md`.
2. Verify external facts (APIs, models, official docs) with `web_search` / `web_fetch`; verify internal claims by reading the code.
Name the source behind the decision.

## Rule 5 — English only

This file, all rules, system prompts, tool schemas and LLM logic are written in English to save BPE tokens. Only the reply to the Master may be Vietnamese.

## Rule 6 — Keep the architecture doc in sync

[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) is the single source of system facts. **Every merge** that changes modules, data stores, model/endpoint config or runtime flow updates it in the same branch. On conflict: ARCHITECTURE.md wins on facts, this file wins on process.

---

## Skills & MCP

Catalog with per-skill triggers, inject mode and MCP server status: [docs/SKILLS_AND_MCP.md](docs/SKILLS_AND_MCP.md). Read it when a task starts, then load **one** matching skill — never the whole catalog. `deepseek-token-budgeter` is always on.

Causal graph schema (3 layers, `MERGE` only, edge types) is defined in [docs/ARCHITECTURE.md §4](docs/ARCHITECTURE.md).
