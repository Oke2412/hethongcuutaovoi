# 🌌 Amazing Nobel — Raphael Life OS

> **"Insight given is insight rejected."**  
> Hệ thống AI cá nhân đóng vai trò "Đại Hiền Giả" (Raphael) giám sát thể trạng, công việc, tâm lý nhân quả, không gian số học H3 và đồng hành cùng Master.

---

### 🎯 Mục Tiêu & Triết Lý
* **Phong thái Mentor:** Trả lời điềm tĩnh, ngắn gọn (1–2 câu) kèm thanh chỉ số HUD: `⚡E | 😐M | ❤️H | 💎Cr | 📍H3`.
* **Ẩn giấu mổ xẻ tâm lý:** Toàn bộ phân tích động cơ ngầm, cơ chế phòng vệ cái tôi (Ego Defense) và khoảng cách $\Delta = \text{Ideal} - \text{Current}$ đều được ẩn kín trong thẻ `<thinking>`.
* **100% Agentic NLP:** Không menu cứng nhắc, AI tự động nhận biết ngữ cảnh và gọi công cụ (Tool Calling).

---

### 🧠 Cốt Lõi Kiến Trúc (Tech Stack)
* **Bộ Não Lập Luận (Dual-Engine):**
  * **DeepSeek V4.1 Flash (`deepseek-flash`):** Đảm nhiệm suy luận chính, tận dụng Context Caching 96.7%, độ trễ ~0.76s, tiết kiệm 87% chi phí.
  * **SiliconFlow:** Chạy mô hình chuyên biệt `Qwen3-Embedding-8B` (4096 chiều) và Cross-Encoder `Qwen3-Reranker-8B`.
* **Bộ Ba Trí Nhớ Tri-Store (GraphRAG):**
  * **Neo4j (Causal Graph):** Đồ thị 3 tầng (Physical, Cognitive, Spatial H3) + Định danh mỏ neo Master và các quan hệ xã hội/sở hữu (`SUPERVISED_BY`, `ROOMMATE_WITH`, `OWNS`, `WORKS_ON`).
  * **Mem0 + ChromaDB (Vector Store):** Lưu giữ sở thích, thói quen cá nhân với cơ chế suy giảm theo thời gian.
  * **SQLite3 FTS5 (Sparse Store):** Tìm kiếm toàn văn siêu tốc transcript âm thanh môi trường với cơ chế **Pointer Linking** (`source_transcript_id`, chi phí 0 token).
* **Định Vị Không Gian (Uber H3 Res 9):** Rời rạc hóa bản đồ thành các ô lục giác ~105m, tự động kích hoạt Side Quests khi đổi vùng.
* **Thói Quen Khoa Học (SM-2):** Thuật toán SuperMemo-2 lặp lại ngắt quãng (thay thế chuỗi Streaks độc hại).

---

### 🖥️ Ranh Giới Frontend (Tauri) vs Backend (PC Cổ)
* **Frontend (Tauri Client):** Thu âm micro, Silero-VAD, Whisper.cpp ASR, TTS/RVC, Giao diện 3D/HUD. Đóng vai trò **MCP Server Host** (mở API điều khiển desktop).
* **Backend (PC Cổ / Home Server):** DeepSeek Flash, Bộ nhớ Tri-Store (Neo4j, SQLite, Chroma), Background Jobs, Động cơ luật. Đóng vai trò **MCP Client** & **Nguồn chân lý duy nhất (Single Source of Truth)**.

---

### 🚀 Lệnh Khởi Chạy Nhanh
```bash
# 1. Chạy toàn bộ hạ tầng bằng Docker Compose
docker compose up -d

# 2. Chạy FastAPI Server cục bộ (port 8000)
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Chạy Telegram Bot long polling
python bot/main.py

# 4. Chạy kiểm thử hồi quy
python tests/test_graph_and_pipeline_fixes.py
python tests/test_desktop_adapter.py
```

---

### 📚 Tài Liệu Kỹ Thuật Đầy Đủ
* 📘 **[Sổ Tay Kỹ Sư & ADRs Toàn Tập (docs/ENGINEERING_NOTEBOOK.md)](docs/ENGINEERING_NOTEBOOK.md)**: 700+ dòng phân tích công thức toán học (SM-2, H3, Reranker, MLA), DDL SQLite FTS5, Cypher queries, 4 sự cố thực chiến và ma trận chi tiết Tauri vs PC Cổ.
* 📜 **[Lịch Sử Tiến Hóa Prompt (PROMPT_HISTORY.md)](PROMPT_HISTORY.md)**: Nhật ký ghi nhận toàn bộ các phiên làm việc và quyết định từ ngày đầu.
