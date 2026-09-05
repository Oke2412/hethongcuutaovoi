# PROMPT_HISTORY.md — L?ch S? Toàn B? Prompt

> **B?T BU?C**: Agent ph?i d?c file này m?i session d? n?m context d?y d?.  
> **Quy t?c ghi:** M?i prompt m?i thêm m?t entry vào cu?i file theo dúng format du?i dây.

---

## Format Entry

```
### [YYYY-MM-DD HH:MM] — <Tóm t?t 1 dòng>
**Prompt:** <Nguyên van prompt c?a ngu?i dùng>
**K?t qu? / Quy?t d?nh:** <Nh?ng gì dã làm ho?c quy?t d?nh t? prompt này>
**Files thay d?i:** <Danh sách file t?o/s?a, ho?c "Không có">
---
```

---

## L?ch S?

### [2026-09-06 01:28] — Kh?i t?o d? án, thi?t k? ki?n trúc t?ng th?
**Prompt:** Tôi dang c?n làm 1 cái app deploy lên con server local ch?y qua tailscale, h? th?ng h? tr? trong cu?c s?ng ki?u phim chuy?n sinh. Ki?n trúc: User ? Telegram Bot ? FastAPI Backend (SQLite, LLM API, Google Calendar). H?i v? reminders (Duolingo-style), free LLM API, Telegram vs app, iPhone.
**K?t qu? / Quy?t d?nh:**
- Stack ch?t: python-telegram-bot + FastAPI + SQLite + Gemini 2.5 Flash + APScheduler + Google Calendar + Docker + Tailscale
- LLM: Gemini 2.5 Flash (primary, free ~1M token/ngày), Groq fallback
- Interface: Telegram Bot (t?t nh?t cho iPhone, không c?n native app)
- Reminders: APScheduler + SM-2 spaced repetition algorithm (không dùng streak)
**Files thay d?i:** Không có (ch? planning)

---

### [2026-09-06 01:34] — B? streak, d?nh nghia tracking nang l?c/th? tr?ng, t?o RULES.md và PROMPT_HISTORY.md
**Prompt:** Ph?n streak không c?n. App c?n bi?t du?c current max, th? tr?ng, ti?n trình công vi?c. T?o 2 file: RULES.md (agent d?c m?i l?n) và PROMPT_HISTORY.md (luu t?t c? prompt d? tracking). C? 2 file d? trong project cho agent d?c, không ph?i app d?c.
**K?t qu? / Quy?t d?nh:**
- Lo?i b? streak/penalty mechanics kh?i design
- App s? track 3 chi?u: (1) Nang l?c t?i da hi?n t?i, (2) Th? tr?ng th? ch?t/tinh th?n, (3) Ti?n trình công vi?c
- T?o RULES.md v?i toàn b? context ki?n trúc + conventions
- T?o PROMPT_HISTORY.md (file này) d? agent tracking
**Files thay d?i:** RULES.md (m?i), PROMPT_HISTORY.md (m?i)

---

### [2026-09-06 01:38] — Scaffold toàn b? project v?i long polling
**Prompt:** ok scaffold di, nhung ch?y long polling nhé
**K?t qu? / Quy?t d?nh:**
- T?o toàn b? c?u trúc project v?i Telegram Bot long polling (drop_pending_updates=True)
- Bot service riêng, API service riêng (Docker Compose 2 service, shared SQLite volume)
- Long polling: `Application.run_polling()` trong `bot/main.py`, không c?n webhook/HTTPS
- ConversationHandler cho /report: 3 lu?ng con (physical status, work progress, capability)
- APScheduler: AsyncIOScheduler timezone Asia/Ho_Chi_Minh
- SM-2 algorithm implement trong `core/memory.py`
- Gemini 2.5 Flash primary, Groq fallback
**Files thay d?i:**
  - requirements.txt (m?i)
  - .gitignore (m?i)
  - .env.example (m?i)
  - config.py (m?i)
  - docker-compose.yml (m?i)
  - Dockerfile (m?i, cho bot)
  - Dockerfile.api (m?i, cho API)
  - db/models.py (m?i): User, CapabilityLog, PhysicalStatus, WorkProject, WorkLog, Memory, Reminder
  - db/database.py (m?i): async SQLite engine + init_db()
  - core/llm.py (m?i): Gemini + Groq fallback + personas
  - core/memory.py (m?i): context builder, SM-2, CRUD helpers
  - core/scheduler.py (m?i): APScheduler, daily check-in, reminder dispatch
  - bot/main.py (m?i): long polling entry point, post_init hook
  - bot/handlers/start.py (m?i)
  - bot/handlers/status.py (m?i): "system screen" display
  - bot/handlers/report.py (m?i): ConversationHandler 13 states
  - bot/handlers/chat.py (m?i): free-text ? LLM
  - api/main.py (m?i): health endpoint
---


### [2026-09-06 01:49] - Quet toan bo project va huong dan su dung
**Prompt:** ok quÃ©t qua rá»“i hÆ°á»›ng dáº«n tÃ´i dÃ¹ng Ä‘i
**Ket qua / Quyet dinh:** Quet toan bo codebase, kiem tra moi truong va huong dan nguoi dung cach setup .env, chay bot va su dung cac tinh nang.
**Files thay doi:** PROMPT_HISTORY.md
---

### [2026-09-06 02:32] - Huong dan day code len GitHub
**Prompt:** gio toi muon day len github thi lam nao?
**Ket qua / Quyet dinh:** Kiem tra git status, gitignore, kiem tra remote va huong dan nguoi dung cac buoc commit, tao repo tren GitHub va push.
**Files thay doi:** PROMPT_HISTORY.md
---