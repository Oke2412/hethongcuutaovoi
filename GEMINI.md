# GEMINI.md — The Ultimate Guide to Raphael Life OS

> **CRITICAL: YOU MUST READ THIS FILE AND `PROMPT_HISTORY.md` BEFORE EVERY SESSION**
> Any AI Agent that ignores this file will be considered in violation of core principles.

---

## 🎯 About the Project
**Project Name:** Amazing Nobel
**Goal:** A "system" style personal AI (Raphael Lord of Wisdom) — tracking physical state, progress, capabilities, and providing reminders through Psychology & Causal analysis. (Insight given is insight rejected).
**Architecture:** 100% Agentic Chat. RAG + GraphRAG (Neo4j) Memory. FastAPI + Docker Compose Backend.

---

## ⚠️ CORE WORKING RULES (MANDATORY)

1. **BRANCH MANAGEMENT (CRITICAL):**
   - **WHENEVER** working on a new feature, function, or logic modification, **ALWAYS create a new branch** (`git checkout -b feature/...`).
   - ONLY push the branch after finishing the code. **NEVER code directly on the `main` branch.**
   - Always run `git status` and `git pull origin main` at the start of every session.

2. **MANDATORY RESEARCH BEFORE ANY DECISION (CRITICAL MANDATORY):**
   - **STRICTLY PROHIBITED TO MAKE ARBITRARY DECISIONS / GUESSING:** Before **ANY** assessment, answer, or code/architecture decision, the Agent **MUST** perform these 2 full research steps:
     1. **STEP 1 - Read `PROMPT_HISTORY.md`:** Carefully read the entire history of recent sessions to thoroughly understand the Master's intent and what previous agents have done. MUST append your own session summary to the end of `PROMPT_HISTORY.md` after every work session.
     2. **STEP 2 - Web Search (`search_web`):** Must use `search_web` to verify official technical docs, latest SOTA leaderboards, and API docs before making a decision.
   - **NO EXCEPTIONS.** All Agent decisions must be based on the two sources above!

3. **STRUCTURE AND SOURCE CODE:**
   - Use `async/await` throughout. Type hints are mandatory.
   - **Unicode Handling:** DO NOT use PowerShell `Set-Content` or here-strings to write files containing Vietnamese/Emojis. Use Python scripts to avoid breaking UTF-8 fonts.
   - DO NOT use ConversationHandler or hardcoded menus. Everything is handled via NLP.

4. **PSYCHOLOGY & CAUSALITY (RAPHAEL DEEP):**
   - Output Mode: Calm, natural like a Mentor. Apply the 3 Anthropic HHH pillars. Keep it brief (1-2 sentences), straight to the point.
   - Always attach the HUD: `⚡E | 😐M | ❤️H | 💎Cr | 📍H3`
   - **Principle of "Insight given is insight rejected":** All deep psychological analysis (Intent Engineering, Motives, Causality) must be hidden inside the `<thinking>` tag.

5. **ENGLISH-ONLY RULES & PROMPTS (TOKEN OPTIMIZATION):**
   - **This file (`GEMINI.md`) and all future rules MUST be written in English.**
   - **100% of System Prompts, System Tools, JSON schemas, and AI logic MUST be written in English** to save BPE tokens. Only the final Output spoken to the Master is allowed to be in Vietnamese.

---

### 🗂️ MANDATORY 3-LAYER JSON RULES (NEO4J SCHEMA)
Whenever updating Neo4j, the system must strictly extract via LLM into this JSON format:
- **Physical Layer:** Person, Location, Object, LifeEvent.
- **Cognitive Layer:** Emotion, DefenseMechanism, CoreBelief.
- **Edges:** TRIGGERS, CAUSES, REINFORCES, MITIGATES, LOCATED_IN, RELATED_TO.
Absolutely use the `MERGE` command instead of `CREATE` in Cypher to avoid Node duplication garbage.

## 🏗️ SYSTEM ARCHITECTURE (AGENT-DRIVEN RAG LOOP)

```text
===========================================================================================================
                                     [ 📱 MASTER / USER ]
                  (Input: Text, Photos, Audio, Live Location H3 Resolution 9)
===========================================================================================================
          |                                                                                  ^
          | (Data Stream)                                                                    | (Execution)
          v                                                                                  |
+---------------------------------------------------------------------------------------------------------+
|                                🛡️ TELEGRAM ADAPTER (bot/main.py & handlers)                               |
|   - Detects Commands, Messages, Images.                                                                 |
|   - Background Trigger: Calculates H3 (Hex) coords -> Compares old/new Hex -> Fires Background Task.    |
+---------------------------------------------------------------------------------------------------------+
          |                                                                                  ^
          v                                                                                  |
===========================================================================================================
                               🧠 CORE BRAIN (core/brain.py) - THE ORCHESTRATOR
===========================================================================================================
|                                                                                                         |
|  [ ⚡ OMNI-AGENTIC LOOP ] (DeepSeek V4.1 Flash via SiliconFlow API)                                     |
|  - Agent continuously loops (while loop) to read context.                                               |
|  - If lacking data, Agent AUTOMATICALLY emits Tool Call: `search_memory_and_causality()`                |
|                                                                                                         |
=========================================================================================|=================
                                                                                         | (Tool Calling)
             +-----------------------------------+---------------------------------------+
             |                                   |                                       |
             v                                   v                                       v
+--------------------------+        +--------------------------+            +--------------------------+
| 🗄️ SQLITE (Database)      |        | 🧬 NEO4J (Causal Graph)  |            | 🧠 MEM0 (Vector Memory)  |
|--------------------------|        |--------------------------|            |--------------------------|
| - Users & MessageLogs    |        | - Causal Nodes           |            | - Qwen3-Embedding-8B     |
| - FTS5 Sparse Search     |        | - H3 Grid Cells          |            |   (4096 Dimensions)      |
|   (Exact Keyword Search) |        | - [:VISITED] Relations   |            | - Semantic Storage       |
+--------------------------+        +--------------------------+            +--------------------------+
             |                                   |                                       |
             | (Top 5 Chunks)                    | (Graph Paths)                         | (Top 5 Chunks)
             +-----------------------------------+---------------------------------------+
                                                 |
                                                 v
===========================================================================================================
                               ⚖️ SCORER & FILTER (Qwen3-Reranker-8B)
                Scores and compresses context. Pumps results back to LLM as Tool Result.
===========================================================================================================
                                                 |
                                                 v (Injected back into Loop Context)
===========================================================================================================
                       ⚡ DEEPSEEK-V4.1-FLASH (CORE CAUSAL & PSYCHOLOGICAL REASONING)
===========================================================================================================
|                                                                                                         |
|  [ HIDDEN <thinking> BLOCK ] (Strictly hidden from Master)                                              |
|  1. Causal Impact: What sensitive past Node does this event trigger? What is the chain reaction?        |
|  2. Psychology Dynamics: What is the Master's hidden motive? (Avoidance, venting, making excuses?)      |
|  3. Intent Engineering: Where is Current State? What is Ideal State? What is the Delta?                 |
|  4. Synthesis: Aggregate the 3 weights above to output Action / Advice.                                 |
|  [ METACOGNITION ]                                                                                      |
|  - The entire content of the AI's <thinking> block is saved back into SQLite, Mem0, and Neo4j           |
|    (as an event attached to the Master's Input). This allows the AI to learn from the past and          |
|    explain its own decisions if questioned by the Master in the future.                                 |
|                                                                                                         |
===========================================================================================================
                                                 |
                   +-----------------------------+-------------------------------+
                   |                                                             |
                   v                                                             v
===========================================================================================================
         [ 🗣️ RAPHAEL'S VOICE (Output) ]                      [ ⚔️ BACKGROUND TRIGGER (Side Quests) ]
===========================================================================================================
| - Format: Concise (1-2 short sentences).     | - Location Hex Transition (Entering a new H3 cell)   |
| - Tone: Calm, respectful, HHH (Anthropic).   | - Energy/Mood Shift (Detecting energy depletion)     |
| - HUD: ⚡E | 😐M | ❤️H | 💎Cr | 📍H3             | - Auto-writes SystemQuest to DB, attaches Penalty    |
| - Action: Push user towards Ideal State.     | - Auto-pushes Notification to Telegram to demand debt|
===========================================================================================================
```

## ⚠️ AGENT TRAUMATIC MEMORIES (MANDATORY TO REMEMBER)
- **API Domain SiliconFlow:** https://api.siliconflow.com (ABSOLUTELY NOT .cn).
- **Core Model:** deepseek-ai/deepseek-v4.1-flash. This model SUPPORTS Thinking Tokens via the hidden `<thinking>` tag. You CAN pass `extra_body={"reasoning_effort": "high"}` to activate deep psychological analysis, or set it to `"none"` if the Master prefers to save costs. It is entirely configurable.
- **Token Optimization:** MANDATORY that 100% of System Prompts, System Tools, schemas, and logic fed to the LLM MUST be written in ENGLISH. Vietnamese consumes a massive amount of BPE Tokens. Only the Output to the Master should be in Vietnamese.
