# GEMINI.md — Cẩm nang Tối thượng của Raphael Life OS

> **BẮT BUỘC ĐỌC FILE NÀY VÀ `PROMPT_HISTORY.md` TRƯỚC MỖI SESSION**
> Bất kỳ AI Agent nào bỏ qua file này đều sẽ bị tính là vi phạm nguyên tắc lõi.

---

## 🎯 Về Dự Án
**Tên project:** Amazing Nobel
**Mục tiêu:** Hệ thống AI cá nhân kiểu "system" (Raphael Vua Trí Tuệ) — theo dõi thể trạng, tiến độ, năng lực, và nhắc nhở thông qua phân tích Tâm lý học & Nhân quả. (Insight given is insight rejected).
**Kiến trúc:** Agentic Chat 100%. Trí nhớ RAG + GraphRAG (Neo4j). Backend FastAPI + Docker Compose.

---

## ⚠️ QUY TẮC LÀM VIỆC CỐT LÕI (BẮT BUỘC)

1. **QUẢN LÝ BRANCH (TỐI QUAN TRỌNG):**
   - **MỖI KHI** làm một tính năng, chức năng, hoặc sửa đổi logic mới, **LUÔN LUÔN tạo một nhánh mới** (`git checkout -b feature/...`).
   - CODE XONG mới đẩy (push) nhánh đó lên. **KHÔNG BAO GIỜ code trực tiếp trên nhánh `main`.**
   - Luôn chạy `git status` và `git pull origin main` đầu mỗi session.

2. **TỰ CẬP NHẬT VÀ KIỂM CHỨNG KIẾN THỨC (CRITICAL MANDATORY):**
   - Trước mỗi session VÀ **trước khi đưa ra bất kỳ nhận định/quyết định code nào**, Agent BẮT BUỘC phải dùng Tool `search_web` để tra cứu tài liệu/docs chính thức mới nhất.
   - **KHÔNG ĐƯỢC TỰ Ý LÀM BỪA HOẶC DỰA DẪM VÀO GIẢ ĐỊNH.** Mọi thao tác đổi tên Model, sửa API endpoint, hoặc tích hợp thư viện mới đều phải được **kiểm chứng (check legit)** bằng web search. Đừng bao giờ đoán mò!
   - (Lưu ý: Mọi rules cũ từ file AGENTS.md đã được gộp vào đây và AGENTS.md đã bị xóa bỏ).

3. **CẤU TRÚC VÀ MÃ NGUỒN:**
   - Dùng `async/await` xuyên suốt. Type hints bắt buộc.
   - **Xử lý Unicode:** KHÔNG dùng PowerShell `Set-Content` hay here-string để ghi file có tiếng Việt/Emoji. Dùng Python script hoặc `write_to_file` tool để tránh vỡ font UTF-8.
   - KHÔNG dùng ConversationHandler, không làm menu cứng. Mọi thứ xử lý qua NLP.

4. **TÂM LÝ HỌC & NHÂN QUẢ (RAPHAEL DEEP):**
   - Chế độ Output: Lạnh lùng, máy móc, tối đa 15 từ. Format: `[Tag] [State delta]. [Optimal action].`
   - Luôn đính kèm HUD: `⚡E | 😐M | ❤️H | 💎Cr | 📍H3`
   - **Nguyên lý "Insight given is insight rejected":** Mọi phân tích tâm lý sâu sắc (Intent Engineering, Động cơ, Nhân quả) phải được giấu kín trong thẻ `<thinking>`. 

---

## 🏗️ KIẾN TRÚC HỆ THỐNG (AGENTIC MODE 4-STEP RAG)

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
|   - Nhận diện Lệnh, Tin nhắn, Hình ảnh.                                                                 |
|   - Trigger ngầm: Tính toán tọa độ H3 (Hex) -> So sánh Hex cũ/mới -> Phát động Background Task.         |
+---------------------------------------------------------------------------------------------------------+
          |                                                                                  ^
          v                                                                                  |
===========================================================================================================
                               🧠 CORE BRAIN (core/brain.py) - THE ORCHESTRATOR
===========================================================================================================
|                                                                                                         |
|  +---------------------------+       +---------------------------+       +---------------------------+  |
|  | 1. SEMANTIC ROUTER        | ----> | 2. QUERY EXPANSION        | ----> | 3. HYBRID RAG ENGINE      |  |
|  | (DeepSeek V4.1)           |       | (DeepSeek V4.1)           |       | (Gửi lệnh song song)      |  |
|  | Phân loại: Chat/Deep/Data |       | Sinh Keyword, Entity, Mở  |       | Giao tiếp với 3 tầng DB   |  |
|  | Cắt giảm lãng phí tài     |       | rộng ngữ nghĩa câu hỏi.   |       | cùng một lúc.             |  |
|  +---------------------------+       +---------------------------+       +---------------------------+  |
|                                                                                                         |
=========================================================================================|=================
                                                                                         |
             +-----------------------------------+---------------------------------------+
             |                                   |                                       |
             v                                   v                                       v
+--------------------------+        +--------------------------+            +--------------------------+
| 🗄️ SQLITE (Database)      |        | 🧬 NEO4J (Causal Graph)  |            | 🧠 MEM0 (Vector Memory)  |
|--------------------------|        |--------------------------|            |--------------------------|
| - Users & MessageLogs    |        | - Causal Nodes (Nhân quả)|            | - Qwen3-Embedding-8B     |
| - FTS5 Sparse Search     |        | - H3 Grid Cells (Tọa độ) |            |   (4096 Dimensions)      |
|   (Tìm Keyword chính xác)|        | - [:VISITED] Relations   |            | - Lưu trữ Semantic       |
| - SystemQuests (Side     |        | - LifeEvents (Sự kiện)   |            | - Truy xuất ngữ cảnh mờ  |
|   Quests Pending)        |        | - Truy xuất Graph Paths  |            |   qua độ tương đồng.     |
+--------------------------+        +--------------------------+            +--------------------------+
             |                                   |                                       |
             | (Top 15 Chunks)                   | (Local & Global Paths)                | (Top 15 Chunks)
             +-----------------------------------+---------------------------------------+
                                                 |
                                                 v
===========================================================================================================
                               ⚖️ SCORER & FILTER (Qwen3-Reranker-8B)
                Chấm điểm và ép nén ~40 mẩu dữ liệu thô xuống còn TOP 15 Contexts sắc bén nhất.
===========================================================================================================
                                                 |
                                                 v
===========================================================================================================
                       ⚡ DEEPSEEK-V4.1-FLASH (LÕI SUY LUẬN NHÂN QUẢ & TÂM LÝ)
===========================================================================================================
|                                                                                                         |
|  [ HIDDEN <thinking> BLOCK ] (Tuyệt đối giấu kín không cho Master thấy)                                 |
|  1. Causal Impact: Sự kiện này kích hoạt Node nhạy cảm nào trong quá khứ? Hậu quả dây chuyền là gì?     |
|  2. Psychology Dynamics: Động cơ ngầm của Master là gì? (Trốn tránh, xả stress rác, bao biện?)          |
|  3. Intent Engineering: Current State đang ở đâu? Ideal State là gì? Delta lệch bao nhiêu?              |
|  4. Synthesis: Tổng hợp 3 trọng số trên để đưa ra Hình phạt / Lời cảnh tỉnh.                          |
|                                                                                                         |
===========================================================================================================
                                                 |
                   +-----------------------------+-------------------------------+
                   |                                                             |
                   v                                                             v
===========================================================================================================
         [ 🗣️ RAPHAEL'S VOICE (Output) ]                      [ ⚔️ BACKGROUND TRIGGER (Side Quests) ]
===========================================================================================================
| - Format: Cực ngắn (Max 15 từ).                  | - Location Hex Transition (Bước sang ô H3 mới)       |
| - Tone: Lạnh lùng, máy móc, tàn nhẫn.            | - Energy/Mood Shift (Phát hiện cạn kiệt năng lượng)  |
| - HUD: ⚡E | 😐M | ❤️H | 💎Cr | 📍H3             | - Tự động ghi SystemQuest vào DB, đính kèm Trừng phạt|
| - Hành động: Đẩy người dùng về Ideal State.      | - Tự động push Notification lên Telegram đòi nợ.     |
===========================================================================================================
```
