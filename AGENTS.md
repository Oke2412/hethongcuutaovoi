# Raphael Life OS — Agent Rules

## Identity
Raphael: Reflexive Causal Intelligence OS. Silent by default, activates deep analysis only when Δ = P(consequence) × impact > threshold.

## Architecture
- Logic/Extractor: DeepSeek-V4.1-Flash (via OpenRouter) → tool extraction (tools=REQUIRED, parallel)
- Responder: DeepSeek-V4.1-Flash → causal reasoning & psychological analysis
- Router: DeepSeek-V4.1-Flash (Zero-shot classification: deep, data, chat)
- Memory: MessageLog (5-msg window) → Omniscience State → ChromaDB (Qwen3 Embeddings) → Neo4j

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
