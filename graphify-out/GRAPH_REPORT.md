# Graph Report - amazing-nobel  (2026-10-20)

## Corpus Check
- 124 files · ~278,300 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 3, .api 1)

## Summary
- 818 nodes · 1827 edges · 47 communities (27 shown, 20 thin omitted)
- Extraction: 88% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 209 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Telegram Bot Handlers
- Agent Turn Execution
- FastAPI Service Shell
- Async Runtime & MCP Stub
- LLM Core & Mem0 Incidents
- Docker Compose Topology
- Core Brain Orchestrator
- Scheduler & Bot Wiring
- Telegram Location Handler
- Project Overview & Memory
- Persona Rules & HUD
- Retrieval & Embedding Stack
- Chronicle Import & Snapshots
- Query Expansion & Neo4j Checks
- GDS Verification Scripts
- Gemini API Reference
- Pipeline Evaluation Harness
- Desktop Adapter Tests
- Location Tracking & SSE
- Skills Catalog & Bridge
- Neo4j GDS Analytics
- System Architecture Overview
- DuckDuckGo Search Parser
- API Route Tests
- Inverted MCP Design
- Reset Command Handlers
- SQLite Migration Script
- Working Rules & Search Skill
- SSE Probe Utility
- Data Wipe Script
- Neo4j Schema Rules
- Desktop Client & DevOps Notes
- DeepSeek Model Migration
- Model Router & Quotas
- Test Report Helper
- DB Session Helper
- Architecture Roadmap & Debt
- Dual Pipeline Split
- Core Value Graph Schema
- Rule File Migration

## God Nodes (most connected - your core abstractions)
1. `get_neo4j_driver()` - 31 edges
2. `User` - 29 edges
3. `SystemQuest` - 25 edges
4. `init_db()` - 22 edges
5. `GDSService` - 19 edges
6. `PhysicalStatus` - 19 edges
7. `_get_llm_client()` - 18 edges
8. `get_or_create_user()` - 18 edges
9. `get_mini_context()` - 18 edges
10. `profile_deep_dive()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `evaluate_location_side_quest()` --conceptually_related_to--> `_process_hex_transition()`  [INFERRED]
  docs/PLAN_location_h3.md → bot/handlers/location.py
- `Asynchronous Graph Ingestion (_persist_to_graph)` --references--> `_persist_to_graph()`  [EXTRACTED]
  docs/ENGINEERING_NOTEBOOK.md → core/brain.py
- `HUD Builder (core/hud.py)` --references--> `build_hud()`  [EXTRACTED]
  docs/PLAN_pipeline.md → core/hud.py
- `Omniscience Context Pre-fetcher (get_mini_context)` --references--> `get_mini_context()`  [EXTRACTED]
  docs/ENGINEERING_NOTEBOOK.md → core/omniscience.py
- `SQLite FTS5 Trigram Virtual Table` --references--> `AmbientTranscript`  [EXTRACTED]
  docs/ENGINEERING_NOTEBOOK.md → db/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Pipeline 1 - Ingestion, Perception & Tri-Store GraphRAG (Input)** — archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_input_master, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_input_tg_adapter, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_input_desktop, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_input_api_gateway, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_input_micro_router, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_input_mcp, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_input_brain_pass1, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_input_gds_service, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_store_sqlite, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_store_mem0, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_store_neo4j, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_cloud_reranker [EXTRACTED 1.00]
- **Pipeline 2 - Cognitive Reasoning, Persona Synthesis & Delivery (Output)** — archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_output_deepseek, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_output_gds_triage, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_output_qwen_embed, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_output_persona, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_output_metacognition, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_output_scheduler, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_output_side_quest, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_output_tg_channel, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_output_desktop_sse, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_output_master [EXTRACTED 1.00]
- **3-Layer Causal Graph Schema (Physical + Cognitive + Edges)** — agents_three_layer_json, dsh_skills_neo4j_gds_expert_skill_three_layer_schema, archify_architecture_raphael_dual_pipeline_20261015_120700_raphael_dual_pipeline_store_neo4j, archify_architecture_raphael_life_os_20261015_115700_raphael_life_os_neo4j_graph [INFERRED 0.85]
- **Tri-Store Hybrid Memory Architecture** — docs_engineering_notebook_tri_store_topology, docs_engineering_notebook_pointer_linking, docs_engineering_notebook_ambient_transcript_fts5, docs_engineering_notebook_mem0_fact_decay, docs_engineering_notebook_reranker_qwen3 [EXTRACTED 1.00]
- **Two-Pass Cognitive Pipeline** — docs_engineering_notebook_agentic_discovery_loop, docs_engineering_notebook_system_orchestrator_prompt, docs_engineering_notebook_system_raphael_prompt, docs_engineering_notebook_hidden_thinking_pipeline, docs_engineering_notebook_metacognition [EXTRACTED 1.00]
- **Latency Optimisation Levers** — docs_latency_breakdown_22s_loop3_write_turn, docs_latency_breakdown_22s_thinking_token_blowup, docs_latency_breakdown_22s_cold_gds_projection, docs_latency_breakdown_22s_neo4j_timeout_failure_mode, docs_sse_thinking_streaming_defer_writes [EXTRACTED 1.00]
- **Mem0 Gemini Provider Configuration Flow** — docs_prompt_history_20260907_2048_hotfix_embedder_mem0, docs_prompt_history_20260907_2048_hotfix_embedder_gemini_embedder_config, docs_prompt_history_20260908_0045_fix_mem0_llm_provider_gemini_llm_config, core_brain, requirements_google_genai [INFERRED 0.85]
- **google-genai Namespace Collision and SDK Migration** — docs_prompt_history_20260907_2238_namespace_conflict_namespace_collision, requirements_google_genai, requirements_google_generativeai, core_llm, core_quest_generator, docs_prompt_history_20260907_2238_namespace_conflict_litellm_bypass [INFERRED 0.85]
- **Spatial Context Engine Components** — docs_prompt_history_20260908_1256_implement_spatial_engine_spatial_context_engine, db_models_spatialstate, core_spatial_haversine, core_spatial_process_location, bot_handlers_location, docs_prompt_history_20260908_1256_implement_spatial_engine_arrived_waypoint_event [EXTRACTED 1.00]

## Communities (47 total, 20 thin omitted)

### Community 0 - "Telegram Bot Handlers"
Cohesion: 0.06
Nodes (55): build_quest_handlers(), handle_quest_callback(), handle_quests(), _bar(), handle(), Settings, build_user_context / save_memory Snippet (UTF-16 dump), _apply_write() (+47 more)

### Community 1 - "Agent Turn Execution"
Cohesion: 0.06
Nodes (16): handle(), _persist_to_graph(), GDSService, rerank_chunks_with_pagerank(), query_causal_graph(), get_neo4j_driver(), init_db(), count_tokens() (+8 more)

### Community 2 - "FastAPI Service Shell"
Cohesion: 0.05
Nodes (29): health(), lifespan(), root(), AmbientTranscriptRequest, chat_endpoint(), chat_health_check(), ChatRequest, _extract_ambient_to_graph_task() (+21 more)

### Community 3 - "Async Runtime & MCP Stub"
Cohesion: 0.05
Nodes (17): handle(), _process_after_delay(), read_local_file(), _AsyncStream, _Choice, _FakeClient, _FakeCompletions, _Fn (+9 more)

### Community 4 - "LLM Core & Mem0 Incidents"
Cohesion: 0.08
Nodes (30): Hotfix: Mem0 Embedder Provider (2026-09-07 20:48), Mem0 memory layer, Hotfix: Mem0 Gemini Embedder SDK (2026-09-07 21:32), ImportError: cannot import name 'genai' from 'google', Fix: Mem0 Gemini Embedder Dependency (2026-09-07 21:37), Namespace Conflict Avoidance (2026-09-07 22:38), Google Namespace Collision (google-genai vs google.generativeai), Hotfix: PERSONAS Syntax Error (2026-09-07 23:17) (+22 more)

### Community 5 - "Docker Compose Topology"
Cohesion: 0.06
Nodes (31): Compose Service: api (FastAPI), Compose Service: bot, Internal Bridge Network, Compose Service: neo4j 5.12 + APOC + GDS, Five GDS Procedures for Structural Intuition, PM-01: ChromaDB Volume Fragmentation, PM-02: Neo4j JVM Startup Race, PM-03: Windows CP1252 / UTF-8 BOM Trap (+23 more)

### Community 6 - "Core Brain Orchestrator"
Cohesion: 0.07
Nodes (23): RaphaelBrain, Agentic Discovery Loop (max 3 iterations), Asynchronous Graph Ingestion (_persist_to_graph), Omniscience Context Pre-fetcher (get_mini_context), ONTOLOGY_PROMPT_TEMPLATE, PM-04: Vietnamese BPE Token Blow-up, Prompt Lifecycle Map (6 prompts), Stress-Test Case Study (TS. Hung and Nam) (+15 more)

### Community 7 - "Scheduler & Bot Wiring"
Cohesion: 0.09
Nodes (15): build_document_handler(), handle_document(), build_onboard_handler(), start_onboard(), auth_check(), main(), post_init(), sm2_next() (+7 more)

### Community 8 - "Telegram Location Handler"
Cohesion: 0.11
Nodes (20): handle_location(), _process_hex_transition(), evaluate_location_side_quest(), get_or_create_spatial_state(), haversine(), haversine_distance(), process_location(), SpatialState (+12 more)

### Community 9 - "Project Overview & Memory"
Cohesion: 0.08
Nodes (18): Amazing Nobel Life OS Project, SQLite FTS5 Trigram Virtual Table, Desktop Companion (Babylon.js + Edge-TTS), Mem0 Preference Overwrite and Fact Decay, Qwen3-Reranker-8B Cross-Encoder Fusion, Telegram Long-Polling Adapter, Tri-Store Hybrid Memory Topology, Timestamps in GraphRAG Memory (+10 more)

### Community 10 - "Persona Rules & HUD"
Cohesion: 0.12
Nodes (9): MCP Server Inventory, Omni-Agentic Loop (Pass 1), Raphael Life OS (Amazing Nobel), Agent-Driven RAG Loop Architecture, Tri-Store Memory, DeepSeek V4.1 Flash, Metacognition Log, Persona Synthesis (+1 more)

### Community 11 - "Retrieval & Embedding Stack"
Cohesion: 0.10
Nodes (17): Qwen3 / BGE Rerank, Pass 1 Orchestrator, Master Input, Micro-Router, Telegram Ingress, Qwen3-Embedding-8B, Mem0 Vector Store, SQLite 3 & FTS5 (+9 more)

### Community 12 - "Chronicle Import & Snapshots"
Cohesion: 0.21
Nodes (12): LifeState, get_or_create_user(), _hash(), import_capabilities(), import_core_psychology(), import_life_events(), import_life_states(), import_memories() (+4 more)

### Community 13 - "Query Expansion & Neo4j Checks"
Cohesion: 0.21
Nodes (6): get_ai_response(), expand_query(), extract_chat(), gather_massive_context(), inject_to_neo4j(), main()

### Community 15 - "Gemini API Reference"
Cohesion: 0.15
Nodes (11): BidiGenerateContent Live API (WebSocket), CreateInteraction (agentic primitive), Gemini API Reference (captured), generateContent (unary REST), streamGenerateContent (SSE), x-goog-api-key Authentication, AVOIDING Edge, Shadow Graph Node (+3 more)

### Community 16 - "Pipeline Evaluation Harness"
Cohesion: 0.25
Nodes (4): init_db(), run_pipeline_evaluation(), test_docker_stack(), run_hard_test()

### Community 18 - "Location Tracking & SSE"
Cohesion: 0.17
Nodes (10): H3 Resolution 9 Location Tracking, Desktop SSE Stream, Master Experience, APScheduler Daemon, Spatial Side-Quest, Telegram Delivery, Background Daemons, Frontend SSE Stream Reader (+2 more)

### Community 19 - "Skills Catalog & Bridge"
Cohesion: 0.18
Nodes (4): Skills Catalog Injection Map, bridge/agent_chat.log, Interactive Actions (click, fill, wait), scrape_page Async Scraper

### Community 20 - "Neo4j GDS Analytics"
Cohesion: 0.20
Nodes (11): GDS Projector, GDS Structural Triage, Neo4j Causal Graph, GDS Analytics Service, Betweenness Centrality Template, Louvain Community Template, Global PageRank Template, Personalized PageRank Ripple Template (+3 more)

### Community 21 - "System Architecture Overview"
Cohesion: 0.18
Nodes (12): FastAPI Gateway, Raphael Core Brain, DeepSeek Flash, Tauri Desktop, Neo4j GDS 2.6.9, Master (User), Mem0 + ChromaDB, Neo4j 5.12 (+4 more)

### Community 22 - "DuckDuckGo Search Parser"
Cohesion: 0.21
Nodes (4): DDGLiteParser, main(), search_duckduckgo_lite(), search_tavily()

### Community 24 - "Inverted MCP Design"
Cohesion: 0.22
Nodes (9): FastAPI Ingress, Desktop Sensors, Inverted MCP Tool, Inverted MCP Server, Inverted MCP Pattern, read_local_file Tool, Minimal Stdio MCP Server Template, validate_safe_path (+1 more)

### Community 25 - "Reset Command Handlers"
Cohesion: 0.27
Nodes (3): build_reset_handlers(), handle_confirm_reset(), handle_reset_request()

### Community 26 - "SQLite Migration Script"
Cohesion: 0.32
Nodes (3): get_existing_columns(), main(), migrate_table()

### Community 29 - "Data Wipe Script"
Cohesion: 0.48
Nodes (4): main(), wipe_chroma(), wipe_neo4j(), wipe_sqlite()

### Community 32 - "DeepSeek Model Migration"
Cohesion: 0.33
Nodes (4): DeepSeek Official API Migration, 12-Turn Context Caching Benchmark, DeepSeek Official API Cut-over, SiliconFlow Migration (.com domain)

### Community 33 - "Model Router & Quotas"
Cohesion: 0.33
Nodes (5): impact_flag (HIGH/LOW) Routing Bit, Model Quota Table (independent pools), Router Layer (regex then embedding), SYSTEM_EXTRACTOR (gemini-3.5-flash-lite), SYSTEM_RAPHAEL_DEEP (causal analysis)

## Ambiguous Edges - Review These
- `Revert: Unsupported Embedder Config (2026-09-07 23:26)` → `Hotfix: Re-add google-genai to requirements (2026-09-08 01:28)`  [AMBIGUOUS]
  docs/prompt_history/20260908_0128_fix_missing_genai_req.md · relation: conceptually_related_to
- `neo4j_test.txt session note (chunk_4.json translation)` → `h3 (geospatial indexing library)`  [AMBIGUOUS]
  neo4j_test.txt · relation: conceptually_related_to

## Knowledge Gaps
- **61 isolated node(s):** `Master Input`, `Desktop Sensors`, `Pipeline 1: Ingestion, Perception & Tri-Store GraphRAG (Input)`, `Pipeline 2: Cognitive Reasoning, Persona Synthesis & Delivery (Output)`, `SQLite + FTS5` (+56 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 269 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GDSService` connect `Agent Turn Execution` to `Telegram Bot Handlers`, `Docker Compose Topology`, `Core Brain Orchestrator`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `User` (e.g. with `build_hud()` and `complete_quest_async()`) actually correct?**
  _`User` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Master Input`, `Desktop Sensors`, `Pipeline 1: Ingestion, Perception & Tri-Store GraphRAG (Input)` to the rest of the system?**
  _61 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Telegram Bot Handlers` be split into smaller, more focused modules?**
  _Cohesion score 0.056442577030812326 - nodes in this community are weakly interconnected._
- **Why does `Five GDS Procedures for Structural Intuition` connect `Docker Compose Topology` to `Agent Turn Execution`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `Revert: Unsupported Embedder Config (2026-09-07 23:26)` and `Hotfix: Re-add google-genai to requirements (2026-09-08 01:28)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `neo4j_test.txt session note (chunk_4.json translation)` and `h3 (geospatial indexing library)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._