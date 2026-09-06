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

### [2026-09-06 04:11] — Lên ý tưởng biến bot giống Raphael và tự sinh System Quest
**Agent:** Antigravity (Gemini 3.1 Pro)
**Prompt:** nghĩ xem nó cần cái gì nữa để giống raphael? và nếu muốn làm nhắc nhở với tự sinh task...
**Kết quả / Quyết định:**
- Git pull origin main thành công.
- Đề xuất thiết kế bảng SystemQuest trong DB.
- Đề xuất tạo một Cronjob chạy vào buổi sáng, gom context gửi LLM sinh JSON nhiệm vụ kèm phần thưởng/hình phạt tự động.
- Thêm nút bấm Inline cho phép user xác nhận hoàn thành và nhận phần thưởng.
**Files thay đổi:** PROMPT_HISTORY.md
---

### [2026-09-06 04:20] — Thảo luận về phản hồi nhiệm vụ khi thiếu context (Function Calling)
**Agent:** Antigravity (Gemini 3.1 Pro)
**Prompt:** à còn kiểu phản ứng với nhiệm vụ nếu thiếu context, như kiểu tôi vốn dĩ đã làm rồi...
**Kết quả / Quyết định:**
- Nhận ra điểm yếu của việc sinh task cứng nhắc là thiếu thương lượng (negotiation).
- Đề xuất nâng cấp LLM thành Agent bằng tính năng Function Calling. Khi người dùng "cãi" hoặc phản hồi lại (ví dụ "tôi cài ROS2 hôm qua rồi"), AI sẽ tự động hiểu, gọi hàm update Memory vào DB, và gọi hàm tái tạo lại Nhiệm vụ mới.
**Files thay đổi:** PROMPT_HISTORY.md
---

### [2026-09-06 04:28] — Code hoàn chỉnh Tính năng Raphael Quest System
**Agent:** Antigravity (Gemini 3.1 Pro)
**Prompt:** ok phang
**Kết quả / Quyết định:**
- Tạo nhánh `feature/system-quests`.
- Bổ sung bảng `SystemQuest` vào `db/models.py`.
- Tạo `core/llm_tools.py` định nghĩa các hàm can thiệp CSDL: `update_memory`, `cancel_quest`, `complete_quest`.
- Refactor `core/llm.py` kích hoạt JSON Function Calling của Gemini 2.5 Flash, giúp bot tự động phân tích chat và gọi tools.
- Thêm `core/quest_generator.py` dùng LLM để tự động phân tích bối cảnh và đẻ ra Nhiệm vụ + Phần thưởng giải trí.
- Gắn lịch cronjob lúc 6:30 sáng vào `core/scheduler.py` để chạy quest generator và báo cáo Telegram.
- Tạo màn hình xem `/quests`.
**Files thay đổi:** db/models.py, core/memory.py, core/llm.py, core/llm_tools.py, core/quest_generator.py, core/scheduler.py, bot/handlers/quest.py, bot/handlers/start.py, bot/main.py, PROMPT_HISTORY.md
---

### [2026-09-06 04:40] — Cập nhật quy tắc làm việc & Bàn về năng lực tính toán của Raphael/Jarvis
**Agent:** Antigravity (Gemini 3.1 Pro)
**Prompt:** giờ thêm vào file rule.md này, mỗi session nếu muốn làm gì đều phải giải thích trước rồi mới chạy...
**Kết quả / Quyết định:**
- Cập nhật `RULES.md` bổ sung 2 quy tắc cốt lõi: (1) Phải giải thích/chốt kế hoạch với người dùng trước khi thực thi; (2) Khi làm tính năng mới luôn phải rẽ nhánh (branch `feature/...`).
- Trả lời người dùng về sức mạnh tính toán cần thiết (Computing Power) để tạo ra một AI thực thụ như Raphael (Slime) hoặc Jarvis (Iron Man) trong thực tế.
**Files thay đổi:** RULES.md, PROMPT_HISTORY.md
---

### [2026-09-06 04:49] — Cập nhật quy tắc Pull Code và Thảo luận Lộ trình xây dựng AI
**Agent:** Antigravity (Gemini 3.1 Pro)
**Prompt:** thêm vào file rules bao giờ cũng phải pull trước mỗi session và check nhánh, giờ tôi có ước mơ như vậy...
**Kết quả / Quyết định:**
- Tạo nhánh `chore/update-rules` để cập nhật `RULES.md` thêm quy định: Phải `git status` và `git pull` trước khi bắt đầu session.
- Đưa ra định hướng lộ trình (Roadmap) kết hợp Giác quan (Edge AI/ROS2) -> Não bộ phần cứng (FPGA/NPU) -> Năng lượng tái tạo.
**Files thay đổi:** RULES.md, PROMPT_HISTORY.md
---

### [2026-09-06 04:59] — Phân tích mô hình Trợ lý giọng nói (Wake word) & Voice Chat
**Agent:** Antigravity (Gemini 3.1 Pro)
**Prompt:** giờ tôi không muốn nhấn nút mà chỉ cần chat với bot là nó biết... với giờ làm nào để nó chạy liên tục như kiểu call msg nhể xong rồi tự động lấy giọng nói...
**Kết quả / Quyết định:**
- Đã chạy `git pull` và merge thành công nhánh `chore/update-rules` vào `main`.
- Giải thích cho user rằng tính năng chat tự nhiên thay cho bấm nút **đã hoạt động** nhờ Function Calling (làm ở phiên trước).
- Đưa ra 2 kiến trúc cho Trợ lý giọng nói: (1) Voice Message qua Telegram; (2) Local Always-on Script (Porcupine Wake Word + Whisper STT + Edge-TTS) chạy trên Edge AI Homelab.
- Đợi user xác nhận trước khi rẽ nhánh code Hướng 1 theo quy định.
**Files thay đổi:** PROMPT_HISTORY.md
---

### [2026-09-06 05:03] — Lên ý tưởng Desktop Popup UI (Giao diện hiển thị máy tính)
**Agent:** Antigravity (Gemini 3.1 Pro)
**Prompt:** không chưa làm vội, tôi còn định làm mỗi lần thông báo thì nó hiện lên toàn màn hình máy tính có được không...
**Kết quả / Quyết định:**
- Đã chạy `git pull` theo quy tắc trước session (code up-to-date).
- Phân tích kỹ thuật: Do Backend chạy trong Docker nên không thể bắn popup trực tiếp lên màn hình Host Windows.
- Đề xuất kiến trúc: Tạo cổng WebSocket trên FastAPI Backend + Code một Desktop Client bằng `tkinter` chạy trên máy host để hứng sự kiện và vẽ cửa sổ nổi (overlay) trên màn hình.
- Đang chờ user duyệt phương án kiến trúc trước khi rẽ nhánh code.
**Files thay đổi:** PROMPT_HISTORY.md
---

### [2026-09-06 18:10] — Húớng dẫn deploy lên Ubuntu Server local
**Agent:** Antigravity (Gemini 3.8 Flash)
**Prompt:** trước khi làm việc nhớ đọc 2 file md ở project, giờ tôi muốn deploy lên server chạy ubuntu server local của tôi kiểu gì?
**Kết quả / Quyết định:**
- Đã đọc kỹ RULES.md và PROMPT_HISTORY.md, chạy `git status` và `git pull` theo đúng quy tắc.
- Hướng dẫn quy trình chuẩn để deploy trên Ubuntu Server (cài Docker, clone repo, config .env, chạy compose, cấu hình systemd/Tailscale).
**Files thay đổi:** PROMPT_HISTORY.md
---

### [2026-09-06 18:44] — Hỗ trợ debug lỗi hethong-bot-1 crash/restart trên Ubuntu Server
**Agent:** Antigravity (Gemini 3.8 Flash)
**Prompt:** hethong-bot-1 hethong-bot "python -m bot.main" bot 2 minutes ago Restarting (1)...
**Kết quả / Quyết định:**
- Hướng dẫn người dùng chạy `docker compose logs bot` để xem log chi tiết nguyên nhân crash (thường do thiếu config token hoặc Conflict polling).
- Giải thích cảnh báo `version is obsolete` trong docker-compose.yml.
**Files thay đổi:** PROMPT_HISTORY.md
---

### [2026-09-06 18:45] — Fix lỗi UnicodeDecodeError ở file .env trên Ubuntu Server
**Agent:** Antigravity (Gemini 3.8 Flash)
**Prompt:** UnicodeDecodeError: 'utf-8' codec can't decode byte 0x97 in position 51: invalid start byte
**Kết quả / Quyết định:**
- Xác định nguyên nhân: File `.env` trên server bị lỗi encoding (không phải UTF-8 chuẩn, thường do copy-paste trên Windows hoặc chứa ký tự lạ).
- Hướng dẫn người dùng cách kiểm tra và tạo lại file `.env` chuẩn UTF-8 không chứa ký tự lạ/dấu Tiếng Việt lỗi font.
**Files thay đổi:** PROMPT_HISTORY.md
---

### [2026-09-06 18:51] — Tiếp tục fix dứt điểm UnicodeDecodeError .env
**Agent:** Antigravity (Gemini 3.8 Flash)
**Prompt:** bot-1 | UnicodeDecodeError: 'utf-8' codec can't decode byte 0x97 in position 51: invalid start byte (lần 2)
**Kết quả / Quyết định:**
- Giải thích: File `.env` trên host server vẫn còn dính byte `0x97` (dấu em-dash `—` hoặc ký tự lạ copy từ Windows sang).
- Cung cấp lệnh One-liner dùng `cat << 'EOF' > .env` để ép ghi đè toàn bộ nội dung sạch bằng ASCII/UTF-8 chuẩn trên Ubuntu bash, không bị lỗi clipboard.
**Files thay đổi:** PROMPT_HISTORY.md
---

### [2026-09-06 18:57] — Sửa lỗi UnicodeDecodeError cho file .env
**Agent:** Antigravity (Gemini 3.1 Pro)
**Prompt:** manh@homeserver:~/hethong$ docker compose logs -f bot ... UnicodeDecodeError: 'utf-8' codec can't decode byte 0x97
**Kết quả / Quyết định:**
- Nhận diện lỗi: File `.env` chứa ký tự dạng cp1252 (ANSI) khiến Pydantic không thể parse bằng chuẩn UTF-8 trong Docker.
- Giải pháp: Chạy script convert file `.env` từ `cp1252` sang `utf-8` nguyên gốc.
- Lưu ý: Không push `.env` lên Github vì vi phạm bảo mật, chỉ push log cập nhật.
**Files thay đổi:** .env (local), PROMPT_HISTORY.md
---
