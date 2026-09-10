# GEMINI.md — Agent Phải Đọc File Này Trước Mỗi Session

> **BẮT BUỘC**: Đọc file này VÀ `PROMPT_HISTORY.md` trước khi làm bất kỳ việc gì trong project.

---

## 🎯 Về Dự Án
**Tên project:** Amazing Nobel
**Mục tiêu:** Hệ thống AI cá nhân kiểu "system" (Raphael Vua Trí Tuệ) — theo dõi thể trạng, tiến độ, năng lực, và nhắc nhở thông qua phân tích Tâm lý học & Nhân học (Insight given is insight rejected).
**Kiến trúc:** Agentic Chat 100%. Trí nhớ RAG + GraphRAG (Neo4j). Backend FastAPI + Docker Compose.

---

## ✅ Quy Tắc Làm Việc Cốt Lõi (BẮT BUỘC)

1. **QUẢN LÝ BRANCH (TỐI QUAN TRỌNG):**
   - **MỖI KHI** làm một tính năng, chức năng, hoặc sửa đổi logic mới, **LUÔN LUÔN tạo một nhánh mới** (`git checkout -b feature/...`).
   - CODE XONG mới đẩy (push) nhánh đó lên. **KHÔNG BAO GIỜ code tính năng mới trực tiếp trên nhánh `main`.**

2. **GIAO TIẾP, ĐỒNG BỘ & TỰ CẬP NHẬT:**
   - Luôn chạy `git status` và `git pull origin main` đầu mỗi session.
   - **TỰ CẬP NHẬT KIẾN THỨC (CRITICAL):** Trước mỗi session, Agent phải dành thời gian `<thinking>` và BẮT BUỘC dùng Tool `search_web` để tra cứu tài liệu mới nhất về các công nghệ đang dùng (DeepSeek, Qwen3, OpenRouter, Mem0) để tránh viết code theo syntax cũ.
   - Luôn giải thích logic định làm trước khi code.
   - Ghi log đầy đủ vào `PROMPT_HISTORY.md` sau khi hoàn thành.

3. **CẤU TRÚC VÀ MÃ NGUỒN:**
   - Dùng `async/await` xuyên suốt. Type hints bắt buộc.
   - **Xử lý Unicode:** KHÔNG dùng PowerShell `Set-Content` hay here-string để ghi file có tiếng Việt/Emoji. Dùng `replace_file_content` hoặc Python `codecs.open` để tránh vỡ font.
   - KHÔNG dùng ConversationHandler, không làm menu cứng. Mọi thứ xử lý qua NLP.

4. **TÂM LÝ HỌC & NHÂN QUẢ (RAPHAEL DEEP):**
   - Raphael phân tích Tâm lý học (Core Value, Shadow, CBT) và Đồ thị Nhân quả kết hợp, đây là các **trọng số** để đưa ra quyết định, chứ không chỉ là "gợi ý tâm lý suông".
   - **Nguyên lý "Insight given is insight rejected":** Mọi phân tích tâm lý sâu sắc phải được giấu kín trong thẻ `<thinking>`. Output gửi cho người dùng chỉ là một hệ quả lạnh lùng hoặc Side Quest kỳ lạ để kích hoạt tự nhận thức (Self-realization).

---

## 🏗️ Kiến Trúc Hệ Thống (Agentic Mode)

```
[User / iPhone / AR Glasses]
     ↓
[Telegram Adapter]
     ↓
[Core Brain - RaphaelBrain]
     ├── [Mem0 / Vector Memory - Qwen3 8B]
     ├── [LLM API - DeepSeek V4.1 Flash via OpenRouter]
     ├── [Neo4j Graph - Causal & Psychology]
     └── [SQLite DB]
```

*File này được duy trì bởi coding agent. Cập nhật khi có quyết định kiến trúc mới.*
