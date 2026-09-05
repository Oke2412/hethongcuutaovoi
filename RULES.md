# RULES.md — Agent Ph?i Ð?c File Này Tru?c M?i Session

> **B?T BU?C**: Ð?c file này VÀ `PROMPT_HISTORY.md` tru?c khi làm b?t k? vi?c gì trong project.

---

## ?? V? D? Án

**Tên project:** Amazing Nobel  
**M?c tiêu:** H? th?ng AI h? tr? cá nhân ki?u "system" trong phim chuy?n sinh — theo dõi th? tr?ng, ti?n d? công vi?c, nang l?c hi?n t?i, l?ch sinh ho?t, và nh?c nh? thông minh.

**Deploy:** Local server ? expose qua Tailscale  
**Interface chính:** Telegram Bot (ngu?i dùng dùng iPhone)  
**Backend:** FastAPI + Docker Compose

---

## ?? Thông Tin Ngu?i Dùng (C?p nh?t liên t?c)

### Nang l?c hi?n t?i (Current Max)
> C?p nh?t m?i khi ngu?i dùng báo cáo ho?c h? th?ng dánh giá l?i.

| Linh v?c | M?c hi?n t?i | Ghi chú |
|---|---|---|
| _(chua có d? li?u)_ | — | C?p nh?t sau khi onboard |

### Th? tr?ng
> Tr?ng thái th? ch?t và tinh th?n g?n nh?t.

- **Ghi nh?n l?n cu?i:** _(chua có)_
- **Tình tr?ng:** _(chua có)_

### Ti?n trình công vi?c
> Các task/project dang ch?y và ti?n d?.

- _(chua có d? li?u — c?p nh?t khi onboard)_

---

## ??? Ki?n Trúc H? Th?ng

```
[User / iPhone]
     ¦
     ?
[Telegram Bot]  ?-- Interface chính
     ¦
     ?
[FastAPI Backend]  (Docker, Local Server, Tailscale)
     ¦
     +-- [SQLite DB]           — Long-term state: memory, stats, goals, logs
     +-- [LLM API]             — Google Gemini 2.5 Flash (primary), Groq (fallback)
     +-- [APScheduler]         — Reminders thông minh, spaced repetition (SM-2)
     +-- [Google Calendar API] — Sync l?ch, t?o event, nh?c vi?c
```

### Stack chính
| Layer | Công ngh? |
|---|---|
| Interface | python-telegram-bot |
| Backend | FastAPI + uvicorn |
| Scheduler | APScheduler (ch?y trong FastAPI process) |
| Database | SQLite + SQLModel (ORM) |
| LLM | Google Gemini 2.5 Flash (free tier) |
| Calendar | Google Calendar API |
| Deploy | Docker Compose |
| Remote Access | Tailscale |

---

## ? Nh?ng Gì KHÔNG Làm

- **Không có streak/penalty mechanics** — ngu?i dùng không mu?n gamification ki?u streak
- **Không làm native iOS app** — dùng Telegram Bot thay th?
- **Không over-engineer** — b?t d?u don gi?n, extend d?n

---

## ? Nh?ng Gì C?N Làm

- H? th?ng nh? context dài h?n (SQLite) — bot ph?i "nh?" ngu?i dùng
- Tracker nang l?c / th? tr?ng / ti?n d? — ngu?i dùng báo cáo, bot ghi nh?n và phân tích
- Reminders thông minh theo SM-2 (dày khi m?i, thua khi quen) — không d?a vào streak
- LLM phân tích và t?ng h?p, không ch? relay thông tin

---

## ?? Coding Conventions

- Language: **Python 3.11+**
- Async: dùng `async/await` xuyên su?t (FastAPI + python-telegram-bot d?u async)
- Type hints: b?t bu?c trên t?t c? function signatures
- Config: dùng `.env` + `pydantic-settings`, không hardcode secrets
- Database: migrations b?ng Alembic n?u schema thay d?i
- Logging: dùng `logging` có format có c?u trúc
- Error handling: không d? exception uncaught ? handler level

---

## ?? C?u Trúc Thu M?c (Target)

```
amazing-nobel/
+-- RULES.md                  ? File này — agent d?c m?i session
+-- PROMPT_HISTORY.md         ? L?ch s? prompt — agent d?c m?i session
+-- docker-compose.yml
+-- .env.example
+-- bot/                      ? Telegram bot handlers
+-- api/                      ? FastAPI routes
+-- core/                     ? Business logic (memory, scheduler, LLM)
+-- db/                       ? SQLite models, migrations
+-- tests/
```

---

*File này du?c duy trì b?i coding agent. C?p nh?t khi có quy?t d?nh ki?n trúc m?i.*
