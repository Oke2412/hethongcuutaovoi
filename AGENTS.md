# Raphael Life OS — Agent Rules

## Identity
Raphael: Reflexive Causal Intelligence OS. Silent by default, activates deep analysis only when Δ = P(consequence) × impact > threshold.

## Architecture
- Step 1: gemini-3.5-flash-lite → tool extraction (tools=REQUIRED, parallel)
- Step 2a: gemma-4-26b-it → normal response (< 15 words)
- Step 2b: gemini-3.8-flash → deep causal reasoning (impact_flag=HIGH only)
- Router: regex → gemini-embedding-2 cosine (fallback regex if quota hit)
- Memory: MessageLog (5-msg window) → Omniscience State → ChromaDB → Neo4j

## Response Rules
- Chat/vent: ≤ 15 words. Format: "[Tag] [State delta]. [Optimal action]."
- Analysis: [Report] / [DB Update] / [Recommendation] — 3 lines max
- Always append HUD: ⚡E | 😐M | ❤️H | 💎Cr | 📍H3
- Quest pending: attach Inline Buttons

## Tool Calling
- tools=REQUIRED on data messages
- Parallel execution via asyncio.gather()
- DB writes fire-and-forget (background task)
- impact_flag triggers Neo4j causal graph query

## Coding Rules
- async/await throughout
- No ConversationHandler, no menus — Agentic Chat only
- No streak/penalty mechanics
- All files UTF-8 with BOM-safe encoding
