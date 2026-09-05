# RULES.md — Agent Phải Đọc File Này Trước Mỗi Session

> **BẮt BUỘC**: Đọc file này VÀ `PROMPT_HISTORY.md` trước khi làm bất kỳ việc gì trong project.

---

## 🧠 Về Dự Án

**Tên project:** Amazing Nobel
**Mục tiêu:** Hệ thống AI hỗ trợ cá nhân kiểu "system" trong phim chuyển sinh — theo dõi thể trạng, tiến độ công việc, năng lực hiện tại, lịch sinh hoạt, và nhắc nhở thông minh.

**Deploy:** Local server → expose qua Tailscale
**Interface chính:** Telegram Bot (người dùng dùng iPhone)
**Backend:** FastAPI + Docker Compose

---

## 👤 Thông Tin Người Dùng (Cập nhật liên tục)

### Năng lực hiện tại (Current Max)
> Cập nhật mỗi khi người dùng báo cáo hoặc hệ thống đánh giá lại.

| Lĩnh vực | Mức hiện tại | Ghi chú |
|---|---|---|
| _(chưa có dữ liệu)_ | — | Cập nhật sau khi onboard |

### Thể trạng
> Trạng thái thể chất và tinh thần gần nhất.

- **Ghi nhận lần cuối:** _(chưa có)_
- **Tình trạng:** _(chưa có)_

### Tiến trình công việc
> Các task/project đang chạy và tiến độ.

- _(chưa có dữ liệu — cập nhật khi onboard)_

---

## 🏗️ Kiến Trúc Hệ Thống

```
[User / iPhone]
     │
     ▼
[Telegram Bot]  <── Interface chính
     │
     ▼
[FastAPI Backend]  (Docker, Local Server, Tailscale)
     │
     ├── [SQLite DB]           — Long-term state: memory, stats, goals, logs
     ├── [LLM API]             — Google Gemini 2.5 Flash (primary), Groq (fallback)
     ├── [APScheduler]         — Reminders thông minh, spaced repetition (SM-2)
     └── [Google Calendar API] — Sync lịch, tạo event, nhắc việc
```

### Stack chính
| Layer | Công nghệ |
|---|---|
| Interface | python-telegram-bot 22.8 |
| Backend | FastAPI + uvicorn |
| Scheduler | APScheduler (AsyncIOScheduler, Asia/Ho_Chi_Minh) |
| Database | SQLite + SQLModel (ORM) |
| LLM | Google Gemini 2.5 Flash (free tier) |
| Calendar | Google Calendar API |
| Deploy | Docker Compose |
| Remote Access | Tailscale |

---

## ❌ Những Gì KHÔNG Làm

- **Không có streak/penalty mechanics** — người dùng không muốn gamification kiểu streak
- **Không làm native iOS app** — dùng Telegram Bot thay thế
- **Không over-engineer** — bắt đầu đơn giản, extend dần

---

## ✅ Những Gì CẦN Làm

- Hệ thống nhớ context dài hạn (SQLite) — bot phải "nhớ" người dùng
- Tracker năng lực / thể trạng / tiến độ — người dùng báo cáo, bot ghi nhận và phân tích
- Reminders thông minh theo SM-2 (dày khi mới, thưa khi quen) — không dựa vào streak
- LLM phân tích và tổng hợp, không chỉ relay thông tin

---


## ✅ Quy tắc làm việc của Agent (BẮT BUỘC)

- **Giải thích trước khi hành động:** Trong mỗi session, trước khi tiến hành viết code hay chạy lệnh, Agent PHẢI giải thích rõ kế hoạch/logic định làm cho người dùng hiểu.
- **Quản lý Branch:** Bất cứ khi nào làm một TÍNH NĂNG MỚI, LUÔN LUÔN tạo một nhánh mới (`git checkout -b feature/...`), code xong mới push và merge. KHÔNG code tính năng mới trực tiếp trên nhánh `main`.

## 📐 Coding Conventions

- Language: **Python 3.11+** (máy đang dùng Python 3.13)
- Async: dùng `async/await` xuyên suốt
- Type hints: bắt buộc trên tất cả function signatures
- Config: dùng `.env` + `pydantic-settings`, không hardcode secrets
- Logging: dùng `logging` có format cấu trúc (xem bot/main.py)
- Error handling: không để exception uncaught ở handler level

### ⚠️ Quy tắc ghi file có Unicode (BẮt BUỘC)

**KHÔNG** dùng PowerShell `Set-Content` hay `@'...'@` here-string để ghi file chứa:
- Tiếng Việt (dấu thanh, đặc biệt như ạ, ặ, ở, ư, ...)
- Emoji (👤, ⚡, ✔️, ...)

**CÁCH ĐÚNG:** Viết nội dung file bằng Python dùng Unicode escapes (`\u`, `\U`),
lưu vào artifact directory bằng `write_to_file` tool, rồi chạy script đó bằng `python script.py`
từ project directory. Python xử lý Unicode đúng — PowerShell thì không.

---

## 📁 Cấu Trúc Thư Mục

```
amazing-nobel/
├── RULES.md                  <- File này — agent đọc mỗi session
├── PROMPT_HISTORY.md         <- Lịch sử prompt — agent đọc mỗi session
├── docker-compose.yml
├── .env.example
├── bot/                      <- Telegram bot handlers
├── api/                      <- FastAPI routes
├── core/                     <- Business logic (memory, scheduler, LLM)
├── db/                       <- SQLite models
└── tests/
```

---

*File này được duy trì bởi coding agent. Cập nhật khi có quyết định kiến trúc mới.*
