# 🌌 AMAZING NOBEL — RAPHAEL LIFE OS (LORD OF WISDOM)

> *"Insight given is insight rejected."*  
> **Raphael Life OS** is an agentic, personal AI system inspired by the "Lord of Wisdom" (Raphael) from *Tensura*. It monitors physical status, work progress, and capabilities while delivering causal psychological insights, habit tracking via SM-2, spatial intelligence via Uber H3, and an advanced Tri-Store GraphRAG memory.

---

## ⚡ CORE CAPABILITIES & HIGHLIGHTS

* **🧠 DeepSeek V4.1 Flash Reasoning Engine:** Powered by DeepSeek Official API (`deepseek-flash`) utilizing 64-token granular Multi-Head Latent Attention (MLA) **Context Caching with 96.7% cache hit rate**, reducing latency to ~0.76s and slashing input token costs by 87%.
* **🧬 Tri-Store Hybrid GraphRAG:**
  * **Neo4j (Causal & Social Graph):** 3-layer ontology (Physical, Cognitive/Psychological, Spatial H3) mapping causal chains (`CAUSES`, `TRIGGERS`) and interpersonal social topology (`SUPERVISED_BY`, `ROOMMATE_WITH`, `OWNS`, `WORKS_ON`).
  * **Mem0 + ChromaDB (Semantic Vector Memory):** Personalized user facts and preferences with biological temporal decay powered by `Qwen3-Embedding-8B` (4096 dimensions).
  * **SQLite3 FTS5 (Sparse & Raw Storage):** Trigram full-text search with **Pointer Linking** (`source_transcript_id`) for lossless, 0-token ambient audio retrieval.
  * **Cross-Encoder Fusion:** `Qwen3-Reranker-8B` dynamically evaluates and compresses 15 multi-store candidates down to the Top 5 most relevant context chunks.
* **📍 Spatio-Temporal Intelligence (Uber H3 Res 9):** Quantizes continuous GPS coordinates into discrete hexagonal cells (~105m edge length). Automatic **Hex Transition Watcher** detects real-world zone changes to trigger contextual Side Quests and health reminders.
* **🔄 SM-2 Spaced Repetition (No Streaks):** Replaces toxic "streak" mechanics with the scientific SuperMemo-2 algorithm to gracefully adapt to human forgetting curves and habit formation without guilt.
* **🖥️ Asymmetric Client-Server Architecture:**
  * **Frontend (Tauri Client):** Handles real-time audio capture, Silero-VAD, Whisper.cpp ASR, and TTS/RVC locally on the edge. Acts as an **MCP Server Host** exposing desktop control tools.
  * **Backend (Home Server / Legacy PC):** Acts as the **MCP Client** and Single Source of Truth, running the Omni-Agentic Brain, Tri-Store memory, and background rule engines.

---

## 🏗️ SYSTEM ARCHITECTURE & DATA FLOW

```text
===========================================================================================================
                                     [ 📱 MASTER / USER ]
                  (Input: Voice Audio, Photos, Text Messages, Live H3 GPS Coords)
===========================================================================================================
               │                                                                    ▲
               ▼                                                                    │ (Voice TTS & HUD)
┌──────────────────────────────────────┐                         ┌──────────────────────────────────────┐
│  🛡️ TELEGRAM ADAPTER (bot/main.py)   │                         │  🌌 DESKTOP COMPANION (Tauri / 3D)   │
│  - Long Polling (PTB 22.8)           │                         │  - Edge Whisper ASR & Silero VAD     │
│  - Location Background Watcher       │                         │  - MCP Server Host (Desktop Control) │
└──────────────────┬───────────────────┘                         └──────────────────▲───────────────────┘
                   │                                                                │
                   ▼                                                                │ (WebSocket / REST)
┌───────────────────────────────────────────────────────────────────────────────────┴───────────────────┐
│                                     🚀 FASTAPI BACKEND (api/main.py)                                  │
│  Endpoints: /api/chat, /api/status, /api/ambient/transcript, /api/ambient/transcripts (FTS5 Search)   │
└──────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                   │
                                                   ▼
===========================================================================================================
                               🧠 CORE BRAIN (core/brain.py) — THE AGENTIC LOOP
===========================================================================================================
│  [ PASS 1: AGENTIC DISCOVERY LOOP ] (DeepSeek Official API - deepseek-flash)                          │
│  - LLM evaluates context. If history/causality is needed, autonomously invokes:                        │
│    `search_memory_and_causality(query)`                                                                │
│                                                                                                         │
│  [ PASS 2: COGNITIVE & PSYCHOLOGICAL SYNTHESIS ]                                                       │
│  - Hidden <thinking>: Causal impact analysis, ego defense extraction, intent delta.                    │
│  - Persona projection: Calm mentor response + HUD metrics (⚡E | 😐M | ❤️H | 💎Cr | 📍H3).              │
=================================================┬=========================================================
                                                 │ Tool Invocation
             ┌───────────────────────────────────┼───────────────────────────────────┐
             ▼                                   ▼                                   ▼
┌─────────────────────────┐         ┌─────────────────────────┐         ┌─────────────────────────┐
│  🧬 NEO4J CAUSAL GRAPH  │         │  🧠 MEM0 + CHROMADB     │         │  🗄️ SQLITE3 FTS5 ENGINE │
│  (GraphRAG)             │         │  (Semantic Vector)      │         │  (Sparse & Raw Storage) │
├─────────────────────────┤         ├─────────────────────────┤         ├─────────────────────────┤
│ • Physical Nodes        │         │ • Qwen3-Embedding-8B    │         │ • MessageLogs           │
│ • Cognitive Nodes       │         │   (4096 dimensions)     │         │ • AmbientTranscript     │
│ • Social Topology       │         │ • Personal Memory Decay │         │ • Full-Text FTS5 Trigram│
│ • Spatial H3 Cells      │         │ • Fast Similarity Search│         │ • SystemQuests & State  │
└────────────┬────────────┘         └────────────┬────────────┘         └────────────┬────────────┘
             │ (Top Subgraph Paths)              │ (Top 5 Chunks)                    │ (Exact Keyword Matches)
             └───────────────────────────────────┼───────────────────────────────────┘
                                                 ▼
===========================================================================================================
                               ⚖️ SCORER & FILTER (Qwen3-Reranker-8B via SiliconFlow)
    Cross-Encoder scoring fuses graph paths, vector chunks, and keyword hits. Injects compressed context back.
===========================================================================================================
```

---

## 📁 REPOSITORY STRUCTURE

```text
amazing-nobel/
├── api/                        # FastAPI Backend Service
│   ├── main.py                 # REST & WebSocket Server Entrypoint
│   └── routes/                 # API Routes (Desktop companion, ambient audio, status)
├── bot/                        # Telegram Bot Adapter
│   ├── main.py                 # Telegram Bot Long Polling Runner (PTB 22.8)
│   ├── handlers/               # Command, chat, report, and location handlers
│   └── ingestion_worker.py     # Background worker for multi-modal ingestion
├── core/                       # Core Cognitive & Reasoning Engine
│   ├── brain.py                # 2-Pass Omni-Agentic Loop & Tri-Store dispatch
│   ├── llm.py                  # DeepSeek & SiliconFlow client orchestration
│   ├── ontology_prompt.py      # 4 Laws of Anti-Spaghetti Graph extraction schema
│   ├── search.py               # Hybrid Tri-Store aggregation & Reranking pipeline
│   ├── memory.py               # SM-2 Spaced Repetition & User Context engine
│   ├── hud.py                  # Real-time HUD string builder (⚡E | 😐M | ❤️H | 💎Cr)
│   └── omniscience.py          # Fast SQLite mini-context pre-fetcher
├── db/                         # Database Models & Connections
│   ├── database.py             # SQLite Async engine & FTS5 virtual tables setup
│   └── models.py               # SQLModel entities (User, Quest, AmbientTranscript, etc.)
├── docs/                       # Architectural & Engineering Knowledge Base
│   ├── ENGINEERING_NOTEBOOK.md # Comprehensive 700+ line Technical Manual & ADRs
│   └── tien_kiep/              # Historical chronicles and extraction records
├── scripts/                    # Ingestion, validation, and maintenance scripts
├── tests/                      # Automated regression & integration test suite
├── docker-compose.yml          # Production Docker Compose v2 stack (Neo4j, Bot, API)
├── Dockerfile                  # Bot container image
├── Dockerfile.api              # FastAPI container image
├── config.py                   # Pydantic Settings & environment validation
├── GEMINI.md                   # Strict AI Agent Principles & Development Guidelines
└── PROMPT_HISTORY.md           # Continuous prompt history & session audit trail
```

---

## 🚀 GETTING STARTED

### Prerequisites
* **Python:** 3.13+
* **Docker & Docker Compose v2:** For containerized Neo4j and microservices.
* **API Keys:**
  * `DEEPSEEK_API_KEY`: From [DeepSeek Official](https://platform.deepseek.com).
  * `SILICONFLOW_API_KEY`: From [SiliconFlow](https://cloud.siliconflow.cn) for Qwen3 Embedder & Reranker.
  * `TELEGRAM_BOT_TOKEN`: From Telegram `@BotFather`.

### 1. Environment Configuration
Create a `.env` file in the root directory:
```env
TELEGRAM_BOT_TOKEN="your_bot_token"
ALLOWED_USER_ID=your_telegram_id

DEEPSEEK_API_KEY="sk-..."
DEEPSEEK_BASE_URL="https://api.deepseek.com"
DEEPSEEK_MODEL="deepseek-flash"

SILICONFLOW_API_KEY="sk-..."
RERANKER_API_URL="https://api.siliconflow.com/v1/rerank"

NEO4J_URI="neo4j://localhost:7687"
NEO4J_USER="neo4j"
NEO4J_PASSWORD="password"

DATABASE_URL="sqlite+aiosqlite:///./data/amazing_nobel.db"
H3_RESOLUTION=9
```

### 2. Run with Docker Compose (Recommended)
```bash
docker compose up -d
```
* **Neo4j Browser:** `http://localhost:7474`
* **FastAPI Docs:** `http://localhost:8000/docs`

### 3. Run Locally for Development
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run FastAPI Server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Run Telegram Bot (in another terminal)
python bot/main.py
```

### 4. Run Test Suite
```bash
python tests/test_graph_and_pipeline_fixes.py
python tests/test_desktop_adapter.py
```

---

## 📖 ARCHITECTURAL DOCUMENTATION

For a deep dive into technical decisions, math proofs, and design trade-offs:
* 📘 **[docs/ENGINEERING_NOTEBOOK.md](docs/ENGINEERING_NOTEBOOK.md)**: 
  * Formal Architectural Decision Records (ADR-01 to ADR-06).
  * Mathematical proofs for SM-2 interval expansion, Uber H3 hexagonal topology, and Cross-Encoder ranking.
  * 4 Real-world Post-Mortem Incident Reports.
  * Asymmetric Tauri Frontend vs Legacy PC Backend Concern Matrix.
* 📜 **[PROMPT_HISTORY.md](PROMPT_HISTORY.md)**: Full evolutionary transcript of every prompt, decision, and engineering milestone.

---

## 🛡️ LICENSE
Private & proprietary. Built with dedication by **Master & Antigravity AI**.
