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

2. **BẮT BUỘC TRA CỨU TRƯỚC TOÀN BỘ MỌI QUYẾT ĐỊNH (CRITICAL MANDATORY):**
   - **NGHIÊM CẤM TỰ Ý RA QUYẾT ĐỊNH / ĐOÁN MÒ / PHÁN BỪA:** Trước **BẤT KỲ** nhận định, câu trả lời, hay quyết định code/kiến trúc nào của bản thân (hoặc khi thấy thiếu context, có thắc mắc/nghi vấn về model, endpoint, logic...), Agent **BẮT BUỘC** phải thực hiện đầy đủ 2 bước tra cứu:
     1. **BƯỚC 1 - Tra cứu `PROMPT_HISTORY.md`:** Đọc kỹ toàn bộ lịch sử các session gần nhất để hiểu thấu đáo ý định của Master và việc các agent trước đã làm. BẮT BUỘC phải cập nhật session của mình vào cuối `PROMPT_HISTORY.md` sau mỗi phiên làm việc.
     2. **BƯỚC 2 - Tra cứu Web (`search_web`):** Bắt buộc dùng `search_web` để kiểm chứng tài liệu kỹ thuật chính thức, bảng xếp hạng SOTA mới nhất và docs API trước khi đưa ra quyết định (tuyệt đối không dựa vào kiến thức cũ bị cutoff).
   - **KHÔNG CÓ NGOẠI LỆ.** Toàn bộ mọi quyết định của Agent đều phải có căn cứ từ 2 nguồn trên, tuyệt đối không được dựa dẫm vào giả định hay suy đoán chủ quan!
   - (Lưu ý: Mọi rules cũ từ file AGENTS.md đã được gộp vào đây và AGENTS.md đã bị xóa bỏ).

3. **CẤU TRÚC VÀ MÃ NGUỒN:**
   - Dùng `async/await` xuyên suốt. Type hints bắt buộc.
   - **Xử lý Unicode:** KHÔNG dùng PowerShell `Set-Content` hay here-string để ghi file có tiếng Việt/Emoji. Dùng Python script hoặc `write_to_file` tool để tránh vỡ font UTF-8.
   - KHÔNG dùng ConversationHandler, không làm menu cứng. Mọi thứ xử lý qua NLP.

4. **TÂM LÝ HỌC & NHÂN QUẢ (RAPHAEL DEEP):**
   - Chế độ Output: Điềm tĩnh, tự nhiên như một Cố vấn (Mentor). Áp dụng 3 trụ cột Anthropic HHH (Helpful, Honest, Harmless). Ngắn gọn 1-2 câu, đi thẳng vào vấn đề.`
   - Luôn đính kèm HUD: `⚡E | 😐M | ❤️H | 💎Cr | 📍H3`
   - **Nguyên lý "Insight given is insight rejected":** Mọi phân tích tâm lý sâu sắc (Intent Engineering, Động cơ, Nhân quả) phải được giấu kín trong thẻ `<thinking>`. 

---

## 🏗️ KIẾN TRÚC HỆ THỐNG (AGENT-DRIVEN RAG LOOP)

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
|  [ ⚡ OMNI-AGENTIC LOOP ] (DeepSeek V4.1 Flash via SiliconFlow API)                                     |
|  - Agent liên tục lặp (while loop) để đọc ngữ cảnh.                                                     |
|  - Nếu nhận thấy thiếu dữ kiện, Agent TỰ ĐỘNG phát ra Tool Call: `search_memory_and_causality()`        |
|                                                                                                         |
=========================================================================================|=================
                                                                                         | (Tool Calling)
             +-----------------------------------+---------------------------------------+
             |                                   |                                       |
             v                                   v                                       v
+--------------------------+        +--------------------------+            +--------------------------+
| 🗄️ SQLITE (Database)      |        | 🧬 NEO4J (Causal Graph)  |            | 🧠 MEM0 (Vector Memory)  |
|--------------------------|        |--------------------------|            |--------------------------|
| - Users & MessageLogs    |        | - Causal Nodes (Nhân quả)|            | - Qwen3-Embedding-8B     |
| - FTS5 Sparse Search     |        | - H3 Grid Cells (Tọa độ) |            |   (4096 Dimensions)      |
|   (Tìm Keyword chính xác)|        | - [:VISITED] Relations   |            | - Lưu trữ Semantic       |
+--------------------------+        +--------------------------+            +--------------------------+
             |                                   |                                       |
             | (Top 5 Chunks)                    | (Graph Paths)                         | (Top 5 Chunks)
             +-----------------------------------+---------------------------------------+
                                                 |
                                                 v
===========================================================================================================
                               ⚖️ SCORER & FILTER (Qwen3-Reranker-8B)
                Chấm điểm và nén ngữ cảnh. Bơm ngược kết quả về cho LLM dưới dạng Tool Result.
===========================================================================================================
                                                 |
                                                 v (Nạp lại vào Context của Vòng lặp)
===========================================================================================================
                       ⚡ DEEPSEEK-V4.1-FLASH (LÕI SUY LUẬN NHÂN QUẢ & TÂM LÝ)
===========================================================================================================
|                                                                                                         |
|  [ HIDDEN <thinking> BLOCK ] (Tuyệt đối giấu kín không cho Master thấy)                                 |
|  1. Causal Impact: Sự kiện này kích hoạt Node nhạy cảm nào trong quá khứ? Hậu quả dây chuyền là gì?     |
|  2. Psychology Dynamics: Động cơ ngầm của Master là gì? (Trốn tránh, xả stress rác, bao biện?)          |
|  3. Intent Engineering: Current State đang ở đâu? Ideal State là gì? Delta lệch bao nhiêu?              |
|  4. Synthesis: Tổng hợp 3 trọng số trên để đưa ra Hành động / Lời khuyên.                           |
|  [ METACOGNITION (SIÊU NHẬN THỨC) ]                                                                     |
|  - Toàn bộ nội dung thẻ <thinking> của AI sẽ được lưu ngược vào SQLite, Mem0, và Neo4j (như một sự kiện |
|    đính kèm với Input của Master). Điều này giúp AI tự học từ quá khứ và có khả năng giải thích lại     |
|    chính quyết định của nó nếu bị Master chất vấn trong tương lai.                                      |
|                                                                                                         |
===========================================================================================================
                                                 |
                   +-----------------------------+-------------------------------+
                   |                                                             |
                   v                                                             v
===========================================================================================================
         [ 🗣️ RAPHAEL'S VOICE (Output) ]                      [ ⚔️ BACKGROUND TRIGGER (Side Quests) ]
===========================================================================================================
| - Format: Súc tích (1-2 câu ngắn).           | - Location Hex Transition (Bước sang ô H3 mới)       |
| - Tone: Điềm tĩnh, tôn trọng, HHH (Anthropic). | - Energy/Mood Shift (Phát hiện cạn kiệt năng lượng)  |
| - HUD: ⚡E | 😐M | ❤️H | 💎Cr | 📍H3             | - Tự động ghi SystemQuest vào DB, đính kèm Trừng phạt|
| - Hành động: Đẩy người dùng về Ideal State.      | - Tự động push Notification lên Telegram đòi nợ.     |
===========================================================================================================
```
