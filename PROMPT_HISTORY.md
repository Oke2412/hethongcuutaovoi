# PROMPT_HISTORY.md — Lịch Sử Toàn Bộ Prompt

> **BẮt BUỘC**: Agent phải đọc file này mỗi session để nắm context đầy đủ.
> **Quy tắc ghi:** Mỗi prompt mới thêm một entry vào cuối file theo đúng format dưới đây.

---

## Format Entry

```
### [YYYY-MM-DD HH:MM] — <Tóm tắt 1 dòng>
**Agent:** <Tên agent thực hiện>
**Prompt:** <Nguyên văn prompt của người dùng>
**Kết quả / Quyết định:** <Những gì đã làm hoặc quyết định từ prompt này>
**Files thay đổi:** <Danh sách file tạo/sửa, hoặc "Không có">
---
```

---

## Lịch Sử

### [2026-09-06 01:28] — Khởi tạo dự án, thiết kế kiến trúc tổng thể
**Agent:** Antigravity (Claude Sonnet 4.6 Thinking)
**Prompt:** Tôi đang cần làm 1 cái app deploy lên con server local chạy qua tailscale, hệ thống hỗ trợ trong cuộc sống kiểu phim chuyển sinh. Kiến trúc: User → Telegram Bot → FastAPI Backend (SQLite, LLM API, Google Calendar). Hỏi về reminders (Duolingo-style), free LLM API, Telegram vs app, iPhone.
**Kết quả / Quyết định:**
- Stack chốt: python-telegram-bot + FastAPI + SQLite + Gemini 2.5 Flash + APScheduler + Google Calendar + Docker + Tailscale
- LLM: Gemini 2.5 Flash (primary, free ~1M token/ngày), Groq fallback
- Interface: Telegram Bot (tốt nhất cho iPhone, không cần native app)
- Reminders: APScheduler + SM-2 spaced repetition algorithm (không dùng streak)
**Files thay đổi:** Không có (chỉ planning)

---

### [2026-09-06 01:34] — Bỏ streak, định nghĩa tracking năng lực/thể trạng, tạo RULES.md và PROMPT_HISTORY.md
**Agent:** Antigravity (Claude Sonnet 4.6 Thinking)
**Prompt:** Phần streak không cần. App cần biết được current max, thể trạng, tiến trình công việc. Tạo 2 file: RULES.md (agent đọc mỗi lần) và PROMPT_HISTORY.md (lưu tất cả prompt để tracking). Cả 2 file để trong project cho agent đọc, không phải app đọc.
**Kết quả / Quyết định:**
- Loại bỏ streak/penalty mechanics khỏi design
- App sẽ track 3 chiều: (1) Năng lực tối đa hiện tại, (2) Thể trạng thể chất/tinh thần, (3) Tiến trình công việc
- Tạo RULES.md với toàn bộ context kiến trúc + conventions
- Tạo PROMPT_HISTORY.md (đây) để agent tracking
**Files thay đổi:** RULES.md (mới), PROMPT_HISTORY.md (mới)

---

### [2026-09-06 01:38] — Scaffold toàn bộ project với long polling
**Agent:** Antigravity (Claude Sonnet 4.6 Thinking)
**Prompt:** ok scaffold đi, nhưng chạy long polling nhé
**Kết quả / Quyết định:**
- Tạo toàn bộ cấu trúc project với Telegram Bot long polling (drop_pending_updates=True)
- Bot service riêng, API service riêng (Docker Compose 2 service, shared SQLite volume)
- Long polling: `Application.run_polling()` trong `bot/main.py`, không cần webhook/HTTPS
- ConversationHandler cho /report: 3 luồng con (physical status, work progress, capability)
- APScheduler: AsyncIOScheduler timezone Asia/Ho_Chi_Minh
- SM-2 algorithm implement trong `core/memory.py`
- Gemini 2.5 Flash primary, Groq fallback
**Files thay đổi:**
  - requirements.txt, .gitignore, .env.example, config.py, docker-compose.yml (mới)
  - Dockerfile, Dockerfile.api (mới)
  - db/models.py, db/database.py, core/llm.py, core/memory.py, core/scheduler.py (mới)
  - bot/main.py, bot/handlers/start.py, bot/handlers/status.py (mới)
  - bot/handlers/report.py, bot/handlers/chat.py, api/main.py (mới)

---

### [2026-09-06 02:12] — Fix lỗi encoding UTF-8 và chạy bot local lần đầu
**Agent:** Antigravity (Claude Sonnet 4.6 Thinking)
**Prompt:** chạy thử local (kèm terminal output báo lỗi utf-8 codec + `__stop_running_marker`)
**Kết quả / Quyết định:**
- Fix lỗi 1: PowerShell ghi file Windows-1252 → strip & re-encode UTF-8
- Fix lỗi 2: PowerShell UTF-8 thêm BOM (U+FEFF) → strip BOM bytes
- Fix lỗi 3: python-telegram-bot 21.3 không support Python 3.13 → upgrade lên PTB 22.8
- Bot chạy thành công với long polling
**Files thay đổi:** requirements.txt (PTB version → 22.8), tất cả .py (BOM removed)

---

### [2026-09-06 02:15] — Fix lỗi hiển thị tiếng Việt bị corrupt trong Telegram
**Agent:** Antigravity (Claude Sonnet 4.6 Thinking)
**Prompt:** tắt bot đi, lỗi định dạng chat (tiếng Việt hiển thị `?` thay vì chữ đúng)
**Kết quả / Quyết định:**
- Root cause: PowerShell here-string ghi Unicode characters bằng code page mặc định của console (CP1252), không phải UTF-8
- Fix: Viết script Python trong artifact dir với nội dung dùng Unicode escapes (`\u`, `\U`), sau đó chạy từ project dir
- Quy tắc mới: **Không dùng PowerShell Set-Content/here-string để ghi file có tiếng Việt hay emoji**. Dùng write_to_file tool (artifact) + chạy Python script.
**Files thay đổi:** bot/handlers/start.py, bot/handlers/status.py, bot/handlers/chat.py, core/llm.py, core/memory.py, core/scheduler.py

---

### [2026-09-06 02:31] — Thêm tên agent vào format PROMPT_HISTORY.md + fix encoding của file này
**Agent:** Antigravity (Claude Sonnet 4.6 Thinking)
**Prompt:** à với cái file lịch sử session thì để tên từng agent vào đó nhé
**Kết quả / Quyết định:**
- Thêm field `**Agent:**` vào format entry và backfill tất cả entries cũ
- Rewrite toàn bộ file bằng Python để fix encoding (file cũ cũng bị corrupt bởi PowerShell)
**Files thay đổi:** PROMPT_HISTORY.md

---


### [2026-09-06 02:38] - Huong dan deploy len server
**Prompt:** ok giờ tôi muốn deploy lên server làm nào?
**Ket qua / Quyet dinh:** Huong dan quy trinh deploy len local server/VPS su dung Docker & Docker Compose (da co san trong project voi 2 service bot + api) ket hop Tailscale.
**Files thay doi:** PROMPT_HISTORY.md
---
### [2026-09-06 03:13] — Tiếp tục công việc từ Claude và hướng dẫn deploy
**Agent:** Antigravity (Gemini 3.1 Pro)
**Prompt:** tiếp tục công việc của claude đi, đọc công việc và lịch sử session trong file md ấy, session nào cũng phải đọc 2 file md nhé, tôi chọn B
**Kết quả / Quyết định:**
- Nhận bàn giao, đọc RULES.md và PROMPT_HISTORY.md.
- Suy luận tuỳ chọn B là tiếp tục quy trình deploy bằng Docker Compose qua Tailscale.
- Hướng dẫn các bước deploy cụ thể.
**Files thay đổi:** PROMPT_HISTORY.md
---

### [2026-09-06 03:23] — Hướng dẫn cách nhập context của bản thân vào bot
**Agent:** Antigravity (Gemini 3.1 Pro)
**Prompt:** tôi muốn input thêm context của bản thân tôi thì làm nào? nhét vào đây à
**Kết quả / Quyết định:**
- Hướng dẫn user không nhập trực tiếp vào file code hay chat thông thường mà sử dụng lệnh `/onboard` trên Telegram bot.
- Ở bước 4 của lệnh `/onboard`, hệ thống sẽ cho phép nhập các thông tin ghi nhớ dài hạn và lưu vĩnh viễn vào Database.
**Files thay đổi:** PROMPT_HISTORY.md
---

### [2026-09-06 03:35] — Thêm /onboard vào lời chào và System Persona
**Agent:** Antigravity (Gemini 3.1 Pro)
**Prompt:** xem lại system đi, chưa có onboard
**Kết quả / Quyết định:**
- Phát hiện ra lệnh `/onboard` chưa được nhắc đến trong `/start` cũng như trong System Prompt (Persona) của LLM.
- Cập nhật `bot/handlers/start.py` để bổ sung `/onboard` vào danh sách lệnh.
- Cập nhật `core/llm.py` để báo cho LLM biết hướng dẫn người dùng dùng lệnh `/onboard` nếu họ muốn lưu context.
**Files thay đổi:** bot/handlers/start.py, core/llm.py, PROMPT_HISTORY.md
---

### [2026-09-06 03:51] — Hỗ trợ chèn lượng lớn context từ file/văn bản dài
**Agent:** Antigravity (Gemini 3.1 Pro)
**Prompt:** tôi muốn input 1 file text hoặc md dài loằng ngoằng được gen từ chat ra để làm context...
**Kết quả / Quyết định:**
- Chạy script python ingest.py băm văn bản dài (1m65 80kg, TKB UET, đồ án ARM/AMR) thành các DB records (Memory, Capability, Physical, Project) và nạp thẳng vào DB SQLite (ID=1).
- Đề xuất tạo thêm tính năng xử lý Document Upload (.txt/.md) với Gemini JSON parsing trong tương lai.
**Files thay đổi:** ingest.py, PROMPT_HISTORY.md
---

### [2026-09-06 03:56] — Thêm tính năng Document Handler trích xuất file .txt/.md
**Agent:** Antigravity (Gemini 3.1 Pro)
**Prompt:** ok, với push lên github, branch sang nhánh khác, làm việc xong rồi push 1 lần nữa
**Kết quả / Quyết định:**
- Chuyển sang nhánh `feature/document-handler`.
- Viết file `bot/handlers/document.py` hỗ trợ xử lý file upload, gửi LLM với `response_mime_type="application/json"` để ép lấy JSON.
- Đăng ký vào `bot/main.py`.
- Push branch lên Github để user có thể pull.
**Files thay đổi:** bot/handlers/document.py, bot/main.py, PROMPT_HISTORY.md
---
