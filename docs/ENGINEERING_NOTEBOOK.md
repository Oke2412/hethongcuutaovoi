# 📘 RAPHAEL LIFE OS — SYSTEM ARCHITECTURE & ENGINEERING NOTEBOOK
> **Tài liệu Kỹ thuật Toàn diện & Hồ sơ Quyết định Kiến trúc (Architectural Decision Records - ADR)**  
> *Dự án:* **Amazing Nobel (Raphael Lord of Wisdom)**  
> *Thời gian phát triển & chuẩn hóa:* 2026-09  
> *Tác giả & Kiến trúc sư:* Master & Antigravity AI  

---

## MỤC LỤC
1. [TỔNG QUAN HỆ THỐNG & TRIẾT LÝ THIẾT KẾ CỐT LÕI](#1-tổng-quan-hệ-thống--triết-lý-thiết-kế-cốt-lõi)
2. [SƠ ĐỒ KIẾN TRÚC TỔNG THỂ (HIGH-LEVEL TOPOLOGY)](#2-sơ-đồ-kiến-trúc-tổng-thể-high-level-topology)
3. [MODULE 1: BỘ NÃO SUY LUẬN & CHIẾN LƯỢC NHÀ CUNG CẤP LLM](#3-module-1-bộ-não-suy-luận--chiến-lược-nhà-cung-cấp-llm)
4. [MODULE 2: BỘ BA TRÍ NHỚ TRI-STORE HYBRID (GRAPHRAG + VECTOR + SPARSE SQL)](#4-module-2-bộ-ba-trí-nhớ-tri-store-hybrid-graphrag--vector--sparse-sql)
5. [MODULE 3: ĐỊNH VỊ KHÔNG GIAN SỐ HỌC (SPATIAL INTELLIGENCE - UBER H3)](#5-module-3-định-vị-không-gian-số-học-spatial-intelligence---uber-h3)
6. [MODULE 4: ĐỘNG CƠ TÂM LÝ HỌC & PHÂN TÍCH NHÂN QUẢ (CAUSAL & INTENT ENGINE)](#6-module-4-động-cơ-tâm-lý-học--phân-tích-nhân-quả-causal--intent-engine)
7. [MODULE 5: GIAO DIỆN & TẦNG ADAPTER ĐA NỀN TẢNG (TELEGRAM & DESKTOP 3D)](#7-module-5-giao-diện--tầng-adapter-đa-nền-tảng-telegram--desktop-3d)
8. [MODULE 6: HẠ TẦNG DEVOPS, CONTAINER & BÀI HỌC THỰC CHIẾN (TRAUMATIC MEMORIES)](#8-module-6-hạ-tầng-devops-container--bài-học-thực-chiến-traumatic-memories)
9. [BẢNG MA TRẬN SO SÁNH QUYẾT ĐỊNH KỸ THUẬT (TRADE-OFF MATRIX)](#9-bảng-ma-trận-so-sánh-quyết-định-kỹ-thuật-trade-off-matrix)
10. [LỘ TRÌNH MỞ RỘNG TƯƠNG LAI (FUTURE ROADMAP)](#10-lộ-trình-mở-rộng-tương-lai-future-roadmap)

---

## 1. TỔNG QUAN HỆ THỐNG & TRIẾT LÝ THIẾT KẾ CỐT LÕI

### 1.1. Sứ Mệnh Của Raphael Life OS
Amazing Nobel không phải là một chatbot hỏi đáp thông thường, cũng không phải một ứng dụng quản lý công việc (To-Do List) đơn giản. Dự án được xây dựng với mục tiêu trở thành **"Trí tuệ Tối cao" (Raphael Lord of Wisdom / Tensura Style)** đóng vai trò một Hệ điều hành Cuộc sống (Life OS) cá nhân:
* Giám sát thể trạng thể chất và tinh thần theo thời gian thực.
* Phân tích căn nguyên sâu xa của các hành vi trì hoãn, ngụy biện, cạn kiệt năng lượng thông qua Tâm lý học Động lực và Đồ thị Nhân quả.
* Kích hoạt các nhiệm vụ phụ (Side Quests) và cơ chế phạt/thưởng tự động khi người dùng di chuyển trong không gian địa lý hoặc có sự thay đổi chỉ số sinh học.

### 1.2. Triết Lý Thiết Kế 1: "Insight Given is Insight Rejected"
Trong tâm lý học ứng dụng, khi một AI chỉ ra thẳng thừng lỗi sai của con người ("Bạn đang lười biếng và ngụy biện"), bản năng phòng vệ cái tôi (Ego Defense Mechanism) sẽ lập tức trỗi dậy, dẫn đến phản ứng bác bỏ thông điệp.
* **Nguyên tắc triển khai:** Toàn bộ quá trình bóc tách tâm lý, phân tích động cơ ngầm (Hidden Motives), định lượng khoảng cách giữa Thực trạng (Current State) và Trạng thái Lý tưởng (Ideal State) **bắt buộc phải ẩn giấu bên trong khối `<thinking>`**.
* **Đầu ra gửi tới Master:** Tuyệt đối ngắn gọn (1–2 câu), giữ phong thái điềm đạm, khiêm nhường như một Mentor, tuân thủ 3 trụ cột Anthropic HHH (Helpful, Honest, Harmless). Kèm theo đó là HUD chỉ số trực quan: `⚡E | 😐M | ❤️H | 💎Cr | 📍H3`.

### 1.3. Triết Lý Thiết Kế 2: 100% Agentic NLP (Loại Bỏ Menus Cứng)
Các hệ sinh thái chatbot truyền thống thường dựa vào máy trạng thái hữu hạn (FSM) như `ConversationHandler`, các menu nút bấm `InlineKeyboardMarkup` cứng nhắc. Cách tiếp cận này tạo ra trải nghiệm người dùng nghèo nàn, gò bó và dễ vỡ khi người dùng nói chuyện tự do.
* **Quyết định kiến trúc:** Toàn bộ tương tác là xử lý ngôn ngữ tự nhiên (NLP) thuần túy. LLM tự động nhận biết ngữ cảnh, tự quyết định gọi công cụ truy vấn trí nhớ (`Tool Calling`) hoặc kích hoạt cập nhật trạng thái mà không cần bất kỳ menu phân nhánh nào.

---

## 2. SƠ ĐỒ KIẾN TRÚC TỔNG THỂ (HIGH-LEVEL TOPOLOGY)

```text
===========================================================================================================
                                     [ 📱 MASTER / USER ]
                  (Input: Voice Audio, Photos, Text Messages, Live H3 GPS Coords)
===========================================================================================================
               │                                                                    ▲
               ▼                                                                    │ (Voice TTS & HUD)
┌──────────────────────────────────────┐                         ┌──────────────────────────────────────┐
│  🛡️ TELEGRAM ADAPTER (bot/main.py)   │                         │  🌌 DESKTOP COMPANION (Tensura 3D)   │
│  - Long Polling (PTB 22.8)           │                         │  - Babylon.js 3D Constellation Graph │
│  - Location Background Watcher       │                         │  - Edge-TTS Neural Voice Generator   │
└──────────────────┬───────────────────┘                         └──────────────────▲───────────────────┘
                   │                                                                │
                   ▼                                                                │ (REST / SSE)
┌───────────────────────────────────────────────────────────────────────────────────┴───────────────────┐
│                                     🚀 FASTAPI BACKEND (api/main.py)                                  │
│  Endpoints: /api/chat, /api/status, /api/ambient/transcript, /api/ambient/transcripts (FTS5 Search)   │
└──────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                   │
                                                   ▼
===========================================================================================================
                               🧠 CORE BRAIN (core/brain.py) — THE AGENTIC LOOP
===========================================================================================================
│  [ PASS 1: AGENTIC DISCOVERY LOOP ] (DeepSeek Official API - deepseek-chat)                            │
│  - LLM evaluates context. If history/causality is needed, autonomously invokes:                        │
│    `search_memory_and_causality(query)`                                                                │
│                                                                                                         │
│  [ PASS 2: COGNITIVE & PSYCHOLOGICAL SYNTHESIS ]                                                       │
│  - Hidden <thinking>: Causal impact analysis, ego defense extraction, intent delta.                    │
│  - Persona projection: Calm mentor response + HUD metrics.                                             │
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

## 3. MODULE 1: BỘ NÃO SUY LUẬN & CHIẾN LƯỢC NHÀ CUNG CẤP LLM

### 3.1. Hành Trình Tiến Hóa (Genesis -> DeepSeek Official)
1. **Giai đoạn 1 (Gemini 2.5 Flash & Groq):** Ban đầu sử dụng Gemini 2.5 Flash miễn phí qua Google AI Studio kết hợp Groq (Llama-3-70B) để dự phòng. Tuy nhiên, Gemini thường xuyên từ chối phân tích tâm lý sâu do rào cản Safety Filters quá nhạy cảm, đồng thời khả năng gọi Tool trả về định dạng JSON nghiêm ngặt bị lỗi cú pháp ngẫu nhiên.
2. **Giai đoạn 2 (SiliconFlow Proxy):** Chuyển sang SiliconFlow để sử dụng `deepseek-ai/deepseek-v4.1-flash`. Dù latency chấp nhận được, nhưng tỉ lệ **Cache Hit Rate** rất thấp và không ổn định do hạ tầng proxy đa người dùng, gây lãng phí chi phí token khi gửi kèm System Prompt dài.
3. **Giai đoạn 3 (DeepSeek Official API - Production):** Nạp quỹ trực tiếp vào `https://api.deepseek.com`, chuyển giao toàn bộ tác vụ lập luận sang `deepseek-chat`.

### 3.2. Benchmark Thực Nghiệm: Cuộc Cách Mạng Context Caching
Vào ngày 30/09/2026, nhóm phát triển đã tiến hành đo đạc benchmark thực nghiệm độc lập với System Prompt tĩnh dài **22,104 ký tự (~5,163 tokens)** kết hợp với câu hỏi động thay đổi qua 12 lượt liên tiếp:

| Lượt Gọi | Loại Yêu Cầu | Cache Hit Tokens | Cache Miss Tokens | Tỉ Lệ Hit | Latency | Chi Phí Input ($/1M token) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Lượt 1** | Ghi Cache mới | 0 | 5,163 | 0% | 1.49s | $0.14 |
| **Lượt 2** | Đọc Cache | 4,992 | 171 | **96.7%** | 0.76s | **$0.014** (Giảm 90%) |
| **Lượt 3-12**| Đọc Cache | 4,992 | 175-180 | **96.6% - 96.8%** | 0.74s - 0.79s | **$0.014** |

**Kết luận kỹ thuật:** 
* DeepSeek tự động lưu cache ở mức phân mảnh 64-token mà không cần cấu hình header phức tạp.
* Giảm hơn **87% tổng chi phí vận hành** và **giảm 50% độ trễ mạng** (từ ~1.5s xuống dưới 0.75s).

### 3.3. Chiến Lược Kiến Trúc Hybrid API (Dual-Engine Strategy)
Thay vì dồn toàn bộ tác vụ cho một nhà cung cấp duy nhất:
* **DeepSeek Official (`https://api.deepseek.com`):** Đảm nhiệm 100% việc lập luận trí tuệ, phân tích tâm lý, bóc tách thực thể JSON, và hội thoại (`deepseek-chat`).
* **SiliconFlow (`https://api.siliconflow.com/v1`):** Giữ lại các mô hình chuyên biệt xử lý biểu diễn vector và xếp hạng:
  * `Qwen/Qwen3-Embedding-8B` (4096 chiều): Tạo vector biểu diễn ngữ nghĩa vượt trội so với các model 1536 chiều cũ.
  * `Qwen/Qwen3-Reranker-8B`: Mô hình Cross-Encoder chuyên dụng để đánh giá độ tương quan ngữ cảnh.

---

## 4. MODULE 2: BỘ BA TRÍ NHỚ TRI-STORE HYBRID (GRAPHRAG + VECTOR + SPARSE SQL)

### 4.1. Tại Sao "Pure Vector RAG" Thất Bại Trong Personal Life OS?
Các hệ thống RAG truyền thống chỉ dùng Vector Database (như Pinecone, Weaviate hay ChromaDB đơn thuần) gặp phải 3 khuyết tật chí mạng:
1. **Mù quáng trước chuỗi nhân quả đa chặng (Multi-hop Blindness):** Vector chỉ đo độ tương đồng ngữ nghĩa về mặt từ vựng. Khi Master hỏi: *"Tại sao tối nay tôi lại thức khuya?"*, Vector DB sẽ tìm các đoạn văn có từ "thức khuya", nhưng hoàn toàn bỏ qua việc trưa thứ Ba bạn cùng phòng làm cháy board mạch, dẫn đến việc sáng thứ Tư thầy giáo dọa đình chỉ đồ án tốt nghiệp.
2. **Trôi dạt ngữ nghĩa (Semantic Drift):** Các từ ngữ mang sắc thái tâm lý tiêu cực (tức giận, lo sợ, tội lỗi) có vector gần nhau, dẫn đến việc LLM nhầm lẫn nguyên nhân cảm xúc này sang cảm xúc khác.
3. **Mất gốc cấu trúc xã hội:** Vector không có khái niệm quan hệ tôn ti. Nó không thể biết "TS. Hùng" là thầy hướng dẫn quyền lực hay chỉ là một người bạn tình cờ gặp.

### 4.2. Bộ Ba Trí Nhớ Tri-Store: Phân Công Nhiệm Vụ

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        TRI-STORE MEMORY SYSTEM                         │
├──────────────────────────┬────────────────────────┬────────────────────┤
│   🧬 NEO4J (GraphRAG)    │  🧠 MEM0 (Vector Store) │ 🗄️ SQLITE3 (Sparse)│
├──────────────────────────┼────────────────────────┼────────────────────┤
│ • Cấu trúc nhân quả      │ • Tương đồng ngữ nghĩa │ • Tìm kiếm FTS5    │
│ • Phân cấp xã hội        │ • Hồ sơ tính cách      │ • Dữ liệu gốc thô  │
│ • Tọa độ không gian H3   │ • Suy giảm theo time   │ • Chi phí 0 token  │
└──────────────────────────┴────────────────────────┴────────────────────┘
```

#### A. Neo4j Causal & Social Graph (Đồ thị Tri thức Động)
Hệ thống sử dụng Neo4j với schema 3 tầng được bóc tách nghiêm ngặt:
* **Tầng Vật lý (Physical Layer):** `Person`, `Location`, `Object`, `LifeEvent`, `Habit`, `WorkProject`.
* **Tầng Nhận thức & Tâm lý (Cognitive Layer):** `Emotion`, `CoreBelief`, `Desire`, `Intention`, `DefenseMechanism`, `ActionStatedDelta`.
* **Tầng Không gian Số học (Spatial Layer):** `H3Cell` (chỉ mục lục giác phân giải 9).
* **Cạnh Quan hệ (Edges):**
  * Nhân quả: `CAUSES`, `TRIGGERS`, `REINFORCES`, `MITIGATES`, `CONTRADICTS`, `LOCATED_IN`.
  * Xã hội & Sở hữu: `SUPERVISED_BY`, `MENTORED_BY`, `ROOMMATE_WITH`, `FRIEND_OF`, `COLLEAGUE_OF`, `OWNS`, `WORKS_ON`, `BORROWS`, `USES`.
* **Quy tắc Bất Biến Chống "Spaghetti Graph":**
  * Luôn sử dụng `MERGE` thay vì `CREATE` trong Cypher để chống phân mảnh thực thể.
  * Mọi Node `Person` bắt buộc phải có thuộc tính `role` và `relationship_to_master` gắn kết với mỏ neo `Master`.
  * Tuyệt đối không sinh Node cho các yếu tố rác ("trời mưa", "sấm chớp", "phong thủy", "sọt rác").

#### B. Mem0 + ChromaDB (Tầng Vector Lưu Giữ Hồ Sơ Cá Nhân)
* Thay vì gọi ChromaDB thô, hệ thống sử dụng thư viện **Mem0** bao bọc bên ngoài.
* Mem0 tự động quản lý các quy luật của trí nhớ sinh học:
  * Trích xuất các sự thật cá nhân (User Preferences / Facts) theo thời gian.
  * Hợp nhất và loại bỏ trùng lặp (Deduplication) khi Master cập nhật thói quen mới.
  * Suy giảm độ ưu tiên của trí nhớ cũ (Temporal Decay).

#### C. SQLite3 + FTS5 & Cơ Chế Pointer Linking
* Để tránh làm phình to GraphRAG bởi các đoạn hội thoại dài hàng nghìn từ, hệ thống triển khai cơ chế **Pointer Linking (Liên kết con trỏ)**:
  * Toàn bộ âm thanh môi trường thu âm từ ứng dụng (`AmbientTranscript`) được nạp nguyên vẹn vào bảng SQLite có kích hoạt **FTS5 Trigram Tokenizer**.
  * Bảng SQLite cho phép tìm kiếm chính xác từng từ khóa, nhãn thiết bị với chi phí 0 token và độ trễ dưới 2ms.
  * Khi DeepSeek bóc tách đồ thị, các Node trong Neo4j chỉ lưu lại ID con trỏ: `source_transcript_id: 142`.
  * Khi cần phục hồi nguyên bản bối cảnh gốc, LLM chỉ việc dùng ID này để kéo toàn văn hội thoại từ SQLite.

#### D. Qwen3-Reranker-8B (Trọng Tài Hợp Nhất Ngữ Cảnh)
* Khi 3 nguồn trả về dữ liệu (Top 5 Graph paths, Top 5 Vector chunks, Top 5 SQLite FTS5 matches), ngữ cảnh sẽ bị phân mảnh và vượt ngưỡng chú ý tối ưu.
* `Qwen3-Reranker-8B` hoạt động như một Cross-Encoder: Chấm điểm tương quan trực tiếp giữa câu hỏi của người dùng và từng đoạn dữ liệu, nén lại thành Top 5 trích dẫn tinh túy nhất trước khi nạp vào vòng lặp của Core Brain.

---

### 4.3. So Sánh Kiến Trúc: Raphael GraphRAG vs. LangGraph vs. Microsoft GraphRAG

Để làm sáng tỏ ranh giới kỹ thuật, bảng đối chiếu dưới đây phân tích sự khác biệt cốt lõi giữa 3 trường phái:

```text
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 BẢNG SO SÁNH BA TRƯỜNG PHÁI GRAPH                                 │
├──────────────────┬─────────────────────────┬──────────────────────────┬───────────────────────────┤
│ Tiêu Chí         │ LangGraph               │ Microsoft GraphRAG       │ Raphael Life OS GraphRAG  │
├──────────────────┼─────────────────────────┼──────────────────────────┼───────────────────────────┤
│ Bản chất cốt lõi │ Agent Orchestration     │ Document RAG Indexer     │ Dynamic Causal & Social   │
│                  │ (State Machine / DAG)   │ (Hierarchical Summaries) │ Memory (Personal Life OS) │
├──────────────────┼─────────────────────────┼──────────────────────────┼───────────────────────────┤
│ Graph là gì?     │ Luồng rẽ nhánh của code │ Đồ thị cụm văn bản       │ Đồ thị tri thức nhân quả  │
│                  │ (Agent -> Tool -> Loop) │ (Entities & Communities) │ tâm lý & không gian H3    │
├──────────────────┼─────────────────────────┼──────────────────────────┼───────────────────────────┤
│ Thuật toán lõi   │ Pregel state graph      │ Leiden Community         │ 3-Layer Causal Schema     │
│                  │ message passing         │ Detection Algorithm      │ + H3 Hexagonal Traversal  │
├──────────────────┼─────────────────────────┼──────────────────────────┼───────────────────────────┤
│ Hình thức nạp    │ Định nghĩa trước trong  │ Batch Processing offline │ Real-time Streaming       │
│ dữ liệu (Ingest) │ mã nguồn Python         │ trên hàng nghìn tài liệu │ (Mỗi tin nhắn / ambient)  │
├──────────────────┼─────────────────────────┼──────────────────────────┼───────────────────────────┤
│ Thế mạnh lớn     │ Quản lý luồng chạy phức │ Trả lời câu hỏi vĩ mô    │ Truy vết căn nguyên tâm   │
│ nhất             │ tạp, Human-in-the-loop  │ (Global Search toàn tập) │ lý, phản hồi tức thì <1s  │
├──────────────────┼─────────────────────────┼──────────────────────────┼───────────────────────────┤
│ Yếu điểm         │ Không phải cơ sở dữ     │ Cực kỳ tốn kém token và  │ Không thiết kế để tóm tắt │
│                  │ liệu để nhớ quá khứ     │ thời gian khi index      │ báo cáo tài chính 1000 tr │
└──────────────────┴─────────────────────────┴──────────────────────────┴───────────────────────────┘
```

---

## 5. MODULE 3: ĐỊNH VỊ KHÔNG GIAN SỐ HỌC (SPATIAL INTELLIGENCE - UBER H3)

### 5.1. Vấn Đề Của Tọa Độ GPS Thuần (Latitude / Longitude)
* **Nhiễu phần cứng (GPS Jitter):** Khi Master ngồi yên một chỗ trong phòng, cảm biến GPS điện thoại vẫn dao động ngẫu nhiên vài mét đến hàng chục mét giữa các lần gửi. Nếu lưu trực tiếp `(lat, lon)`, cơ sở dữ liệu sẽ bị tràn ngập bởi hàng trăm tọa độ rác khác nhau.
* **Không thể lập chỉ mục đồ thị hiệu quả:** Tọa độ thực `(21.00412, 105.84311)` là dữ liệu liên tục (continuous), không thể dùng làm khóa định danh (Discrete Key) cho các Node đồ thị để thực hiện các phép nối quan hệ `[:LOCATED_IN]`.

### 5.2. Giải Pháp: Uber H3 Hexagonal Hierarchical Spatial Index
Hệ thống chuẩn hóa toàn bộ không gian Trái Đất về các ô lục giác đều **Uber H3 ở Phân giải 9 (Resolution 9)**:
* Kích thước mỗi ô lục giác: Đường kính ~100m, diện tích xấp xỉ 0.1 km² (vừa vặn với quy mô một tòa nhà, quán cafe, khuôn viên trường học hoặc xưởng chế tạo).
* Tọa độ được rời rạc hóa thành một chuỗi Hex duy nhất (ví dụ: `892f58609b7ffff`).

```text
       / \         / \
      /   \       /   \
     | H3  |-----| H3  |   <-- Không gian được lượng tử hóa thành
      \ 9 /       \ 9 /        các Node đồ thị rời rạc [H3Cell]
       \ /         \ /
        |   Master  |
        |  Di chuyển|
        v           v
   Hex Transition Event -> Kích hoạt Background Task sinh Nhiệm Vụ (Side Quest)
```

### 5.3. Cơ Chế Bắt Sự Kiện Chuyển Ô (Hex Transition Watcher)
1. Khi Telegram Adapter hoặc Desktop App gửi vị trí, hệ thống tính toán mã H3 tương ứng.
2. So sánh mã H3 mới với mã H3 lưu trong SQLite session của Master.
3. Nếu phát hiện chuyển đổi ô (`old_hex != new_hex`):
   * Lưu quan hệ `(Master)-[:VISITED {timestamp: now()}]->(H3Cell)`.
   * Truy vấn đồ thị xem ô H3 mới có gắn với địa điểm nhạy cảm nào không (ví dụ: quán cafe quen, phòng gym, xưởng chế tạo).
   * Kích hoạt tiến trình ngầm kiểm tra năng lượng: Nếu phát hiện năng lượng thấp (`Energy < 4/10`) mà bước vào ô làm việc, tự động sinh nhiệm vụ nghỉ ngơi kèm cảnh báo nợ thể trạng.

---

## 6. MODULE 4: ĐỘNG CƠ TÂM LÝ HỌC & PHÂN TÍCH NHÂN QUẢ (CAUSAL & INTENT ENGINE)

### 6.1. Cấu Trúc Khối Suy Ngẫm Ẩn (`<thinking>`)
Trong mỗi lượt xử lý của `core/brain.py`, DeepSeek thực thi 4 bước lý luận nội tâm:
1. **Causal Impact (Tác động Nhân quả):** Sự kiện vừa xảy ra kích hoạt những mắt xích nhạy cảm nào trong quá khứ? (Ví dụ: Việc hỏng vi điều khiển kích hoạt nỗi sợ trễ tiến độ đồ án tốt nghiệp).
2. **Psychology Dynamics (Cơ chế Phòng vệ Cái tôi):** Master đang có động cơ ngầm nào? Có đang dùng cơ chế hợp lý hóa (Rationalization), thoái thác (Avoidance) hay đóng vai nạn nhân không?
3. **Intent Engineering (Kỹ nghệ Ý đồ):** 
   $$\Delta = \text{Ideal State} - \text{Current State}$$
   Cần tạo ra lực đẩy gì để thu hẹp khoảng cách này mà không làm Master tự ái?
4. **Synthesis (Tổng hợp):** Đúc kết thành 1–2 câu hướng dẫn mang phong thái bình thản của Raphael kèm HUD chỉ số.

### 6.2. Metacognition: Trí Nhớ Về Quá Trình Suy Nghĩ Của Chính AI
Toàn bộ nội dung bên trong thẻ `<thinking>` không bị vứt bỏ sau khi sinh câu trả lời. Nó được lưu ngược vào SQLite và gắn nhãn thành một thực thể `MetacognitiveEvent` trong Neo4j.
* **Lợi ích kiến trúc:** Khi Master thắc mắc *"Tại sao hôm qua ngươi lại khuyên ta dừng code Rust để đi ngủ?"*, Raphael có thể truy vấn lại chính suy nghĩ trong quá khứ của mình để giải trình minh bạch: *"Báo cáo Master: Lúc đó nhịp tim người đo được 110 bpm và việc format máy chỉ là hành vi trốn chạy áp lực thi cử"*.

---

## 7. MODULE 5: GIAO DIỆN & TẦNG ADAPTER ĐA NỀN TẢNG (TELEGRAM & DESKTOP 3D)

### 7.1. Telegram Adapter (`bot/`)
* **Framework:** `python-telegram-bot` phiên bản 22.8 (tương thích hoàn toàn Python 3.13).
* **Cơ chế Long Polling:** `Application.run_polling(drop_pending_updates=True)`. Lý do chọn Long Polling thay vì Webhook:
  * Hệ thống chạy trên mạng nội bộ cục bộ (Local Server) kết nối qua **Tailscale VPN**.
  * Long Polling không đòi hỏi phải mở cổng công khai (Port Forwarding), không cần mua tên miền hay cấu hình chứng chỉ SSL/HTTPS phức tạp.
* **Xử lý đa phương tiện:** Tự động bắt ảnh gửi về, trích xuất tọa độ GPS trực tiếp từ chức năng Live Location của điện thoại.

### 7.2. Desktop Companion & Kiến Trúc Tách Rời (Separation of Concerns)
Desktop App (`tensurafrontend`) được thiết kế theo mô hình **Tầng Giao Diện Mỏng (Thin Presentation Layer)**:
* **Frontend:** Viết bằng giao diện 3D (Babylon.js) mô phỏng chòm sao tri thức và kết nối giọng nói Edge-TTS.
* **Backend:** Nằm hoàn toàn tại `amazing-nobel` qua các API REST:
  * `POST /api/chat`: Xử lý hội thoại văn bản.
  * `POST /api/ambient/transcript`: Nhận luồng âm thanh phiên âm từ micro máy tính.
  * `GET /api/ambient/transcripts`: Tìm kiếm nhanh lịch sử hội thoại bằng FTS5.
  * `GET /api/status`: Lấy trạng thái HUD thời gian thực.

---

## 8. MODULE 6: HẠ TẦNG DEVOPS, CONTAINER & BÀI HỌC THỰC CHIẾN (TRAUMATIC MEMORIES)

### 8.1. Docker Compose v2 Orchestration
Hệ thống được đóng gói thành cụm 3 container phối hợp chặt chẽ:
```yaml
services:
  neo4j:
    image: neo4j:5.23.0
    healthcheck:
      test: ["CMD-SHELL", "cypher-shell -u neo4j -p password 'RETURN 1'"]
      interval: 10s
      retries: 10
  bot:
    build: { context: ., dockerfile: Dockerfile }
    depends_on:
      neo4j: { condition: service_healthy }
  api:
    build: { context: ., dockerfile: Dockerfile.api }
    volumes:
      - ./data/chroma:/app/chroma_db
    depends_on:
      neo4j: { condition: service_healthy }
```

### 8.2. Những Bài Học Xương Máu Trong Quá Trình Phát Triển (Traumatic Memories)

#### 1. Lỗ Hổng Đồng Bộ ChromaDB Giữa Các Container
* *Sự cố:* Container `bot` lưu vector vào `./chroma_db` nội bộ, trong khi container `api` lại khởi tạo một thư mục trống khác trong image của nó. Khi Desktop App gọi API thì không tìm thấy ký ức mà Bot vừa ghi nhận.
* *Khắc phục:* Mount chung một thư mục volume máy chủ `- ./data/chroma:/app/chroma_db` cho toàn bộ các service.

#### 2. Hiện Tượng Đua Tốc Độ Khởi Động (Neo4j Race Condition)
* *Sự cố:* Container Python khởi động trong 1 giây và lập tức kết nối tới Neo4j. Trong khi đó, Neo4j JVM cần 15–20 giây để khởi động database engine. Kết quả: Bot bị crash liên tục với lỗi `ServiceUnavailable: Unable to retrieve routing information`.
* *Khắc phục:* Viết script `healthcheck` chạy lệnh Cypher thực thụ kiểm tra Neo4j sẵn sàng 100%, kết hợp `condition: service_healthy` trong `depends_on`.

#### 3. Bẫy Mã Hóa Ký Tự Windows CP1252 & PowerShell UTF-8 BOM
* *Sự cố:* Trên hệ điều hành Windows, PowerShell mặc định ghi file bằng bảng mã Windows-1252 hoặc UTF-8 kèm Byte Order Mark (BOM: `\xEF\xBB\xBF`). Điều này khiến tiếng Việt có dấu biến thành ký tự rác (`?` hoặc ``) và làm gãy trình biên dịch Python 3.13.
* *Quy tắc vĩnh viễn:* **Nghiêm cấm dùng PowerShell Set-Content hoặc here-strings để tạo file có tiếng Việt/Emoji**. Toàn bộ việc ghi file văn bản phải được thực hiện bằng Python script với cờ `encoding='utf-8'` rõ ràng.

#### 4. Quy Tắc Giảm Tiêu Hao Token Bằng Tiếng Anh (Token Optimization)
* *Sự cố:* Các file cấu hình, System Prompts và định nghĩa Tool ban đầu viết bằng tiếng Việt. Thuật toán phân rã Byte-Pair Encoding (BPE) của LLM biến một từ tiếng Việt có dấu thành 3–5 token (thay vì 1 token như tiếng Anh), gây bùng nổ chi phí context và làm chậm tốc độ suy luận.
* *Quy tắc chuẩn hóa:* **100% System Prompts, Ontology Schemas, Tool Calling Definitions và Rules phải viết hoàn toàn bằng TIẾNG ANH**. Chỉ duy nhất câu trả lời cuối cùng gửi tới Master mới dùng tiếng Việt.

---

## 9. BẢNG MA TRẬN SO SÁNH QUYẾT ĐỊNH KỸ THUẬT (TRADE-OFF MATRIX)

| Thành Phần | Công Nghệ Lựa Chọn | Phương Án Bị Loại Bỏ | Lý Do Lựa Chọn & Đánh Đổi (Trade-off) |
| :--- | :--- | :--- | :--- |
| **Cốt Lõi Lập Luận** | **DeepSeek Official API** (`deepseek-chat`) | SiliconFlow Proxy, Gemini Flash, Groq | Tận dụng Context Caching 96.7% giúp giảm 87% chi phí. Khả năng reasoning sâu, tuân thủ schema JSON tuyệt đối và không bị chặn bởi bộ lọc nội dung quá nhạy cảm. |
| **Đồ Thị Tri Thức** | **Neo4j Enterprise/Community** | Memgraph, NetworkX, PostgreSQL Tuples | Neo4j sở hữu ngôn ngữ Cypher hoàn thiện nhất, hệ sinh thái APOC mạnh mẽ, hỗ trợ đồ thị thuộc tính (LPG) chuẩn xác cho chuỗi nhân quả và không gian H3. |
| **Vector Memory** | **Mem0 + ChromaDB** | Raw Chroma, Pinecone, Milvus | Mem0 cung cấp sẵn logic quản lý trí nhớ cá nhân (trích xuất User Facts, khử trùng lặp và suy giảm theo thời gian) thay vì phải tự viết giải thuật trên Vector DB thô. |
| **Tìm Kiếm Từ Khóa**| **SQLite3 FTS5 Trigram** | Elasticsearch, Meilisearch | Không tốn thêm RAM chạy JVM (như ES), cấu hình nằm gọn trong 1 file DB duy nhất, tốc độ truy vấn từ khóa dưới 2ms với chi phí 0 token. |
| **Định Vị Không Gian**| **Uber H3 (Resolution 9)** | Tọa độ GPS Lat/Lon thô, Geohash | H3 có các ô lục giác đều (không bị biến dạng diện tích như hình chữ nhật của Geohash), giúp lượng tử hóa không gian thành các Node rời rạc để phát hiện sự kiện đổi vùng tức thì. |
| **Điều Phối Luồng** | **Custom Omni-Agentic Loop** | LangGraph, CrewAI, AutoGen | Tự chủ hoàn toàn mã nguồn vòng lặp trong `core/brain.py`, không bị phụ thuộc vào sự phình to (bloatware) và các thay đổi breaking changes liên tục của framework bên thứ ba. |
| **Kênh Giao Tiếp** | **Telegram Long Polling** | Telegram Webhook, Custom iOS App | Dễ dàng kết nối từ xa qua Tailscale VPN mà không cần Public IP/Domain/SSL. Bỏ qua quy trình duyệt ứng dụng phức tạp của Apple App Store. |

---

## 10. LỘ TRÌNH MỞ RỘNG TƯƠNG LAI (FUTURE ROADMAP)

1. **Chu kỳ Củng cố Trí nhớ Ban đêm (Memory Consolidation & Dream Cycle):**
   * Triển khai tiến trình chạy ngầm vào lúc 3:00 sáng hàng ngày để rà soát toàn bộ đồ thị Neo4j.
   * Chạy các giải thuật nén đồ thị: Gom cụm các sự kiện nhỏ lẻ trong ngày thành một Node `LifeEpisode` lớn, cắt tỉa các cạnh quan hệ tạm thời không quan trọng để giữ Graph luôn tinh gọn qua nhiều năm tháng.
2. **Audio Streaming Pipeline Trực Tiếp Từ Thiết Bị Đeo (Wearable Integration):**
   * Nâng cấp endpoint `/api/ambient/transcript` hỗ trợ nhận luồng âm thanh trực tiếp (WebRTC / WebSocket) từ phần cứng vòng đeo tay hoặc kính thông minh, tự động phát hiện giọng nói Master qua mô hình nhận diện giọng nói (Voice Biometrics).
3. **Mô Hình Lập Luận Cục Bộ On-Device (Edge Fallback):**
   * Đóng gói một model LLM lượng tử hóa nhỏ (như Qwen2.5-3B hoặc DeepSeek-R1-Distill-1.5B) chạy trực tiếp trên card đồ họa máy tính để hệ thống vẫn duy trì khả năng đối đáp cơ bản khi mất kết nối Internet.

---
*Bản quyền kiến trúc thuộc về Master & Raphael Life OS Development Team.*  
*Tài liệu được lưu trữ vĩnh viễn tại `docs/ENGINEERING_NOTEBOOK.md`.*
