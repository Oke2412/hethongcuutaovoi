---
name: deepseek-token-budgeter
description: >-
  Rules, API configurations, and token optimization strategies for DeepSeek models
  (V3, V4.1 Flash, R1) via SiliconFlow and direct APIs. Use this skill when configuring
  reasoning effort, managing thinking budgets (1000-3000 words vs disabled), minimizing latency,
  preventing output token explosion, or optimizing BPE token consumption.
---

# DeepSeek Token Budgeter & Reasoning Controller

This skill governs the token economics, reasoning depth, and latency optimization for DeepSeek V3, V4.1 Flash, and DeepSeek R1 models deployed on SiliconFlow or DeepSeek Platform.

## Core Economic Invariant (Reasoning Tokens = Output Tokens)

> [!IMPORTANT]
> DeepSeek bills all `reasoning_tokens` (thinking tokens) as **Output/Completion Tokens** at the highest rate.
> If thinking is enabled on every tool call or extraction pass, output tokens will explode (e.g. 250,000+ tokens/hour) and latency will exceed 60-100 seconds per turn.

---

## 1. Selective Thinking Rules (When to Suppress vs When to Enable)

### Case A: STRICTLY DISABLE Thinking (`thinking: disabled`)
Apply to any deterministic, intermediate, or tool-calling pass:
- **Pass 1 Tool Calling Loop (Orchestrator)**: Tool decisions must be instant.
- **Ontology JSON Extraction**: BPE extraction into 3-tier entities.
- **Micro-Router / Classification**: Answering simple YES/NO or routing queries.

```python
# Pass 1 & Extraction configuration:
response = await client.chat.completions.create(
    model="deepseek-ai/deepseek-v4.1-flash",
    messages=messages,
    tools=TOOLS_DEF,
    temperature=0.0,
    max_tokens=1024,
    extra_body={"thinking": {"type": "disabled"}}  # <-- CRITICAL: Disables reasoning tokens
)
```

### Case B: ENABLE Deep Thinking (Pass 2 Persona & Causal Triage)
Thinking is explicitly permitted and encouraged in **Pass 2 Persona Synthesis**:
- **Reasoning Depth**: 1,000 to 3,000 words is acceptable when solving multi-crisis triage (P0 biological survival vs academic/interpersonal conflicts).
- **Configuration**:
```python
# Pass 2 Deep Cognitive Reasoning:
response2 = await client.chat.completions.create(
    model="deepseek-ai/deepseek-v4.1-flash",
    messages=[
        {"role": "system", "content": SYSTEM_RAPHAEL},
        {"role": "user", "content": raphael_prompt}
    ],
    max_tokens=4000,
    temperature=0.0,
    extra_body={"reasoning_effort": "high"}  # or "low" for routine turns
)
```

---

## 2. SiliconFlow API Best Practices

- **Official Domain**: `https://api.siliconflow.com/v1` (ABSOLUTELY NEVER use `.cn`).
- **Core Models**:
  - `deepseek-ai/deepseek-v4.1-flash` (Primary Fast Cognitive LLM)
  - `Qwen/Qwen3-Embedding-8B` (4096-dimensional dense embeddings)
  - `Qwen/Qwen3-Reranker-8B` or `BAAI/bge-reranker-v2-m3` (Cross-encoder reranking)

---

## 3. BPE Token Conservation (English vs Vietnamese)

- **System Prompts & Tool Definitions**: Must be written in **100% English**. Vietnamese characters consume 2.5x to 4x more BPE tokens per word due to diacritics.
- **Master-Facing Output**: Only the final response delivered to the user is in Vietnamese. Keep it razor-sharp (1-2 sentences).
