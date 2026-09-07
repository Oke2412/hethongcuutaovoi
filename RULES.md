# RULES.md — Agent Phải Đọc File Này Trước Mỗi Session

> **BẮT BUỘC**: Đọc file này VÀ `PROMPT_HISTORY.md` trước khi làm bất kỳ việc gì trong project.

---

## 🎯 Về Dự Án

**Tên project:** Amazing Nobel
**Mục tiêu:** Hệ thống AI hỗ trợ cá nhân kiểu "system" trong phim chuyển sinh — theo dõi thể trạng, tiến độ công việc, năng lực hiện tại, lịch sinh hoạt, và nhắc nhở thông minh.
**Kiến trúc:** Agentic Chat 100% (Không dùng luồng Menu/Q&A cứng). Hệ thống sở hữu "Trí nhớ vô hạn" nhờ RAG + Liên kết ngữ cảnh.
**Interface chính:** Telegram Bot (người dùng dùng iPhone). Tương lai: Kính AR / Neural Chip.
**Backend:** FastAPI + Docker Compose.

---

## 🏗️ Kiến Trúc Hệ Thống Hiện Tại (Agentic Mode)

```
[User / iPhone / AR Glasses]
     ↓
     ↑
[Frontend Adapter (Telegram / Audio / Vision)]  <—— Hứng dữ liệu đầu vào
     ↓
     ↑
[Core Brain - RaphaelBrain] (core/brain.py)  <—— Xử lý toàn bộ logic, gọi Tools, lấy ký ức
     ├── [Mem0 / RAG Memory Layer]           <—— Bới móc ký ức, lưu trữ Vector
     ├── [LLM API - Gemini 3.8 Flash]        <—— Não chính phân tích ý định
     ├── [SQLite DB]                         <—— Dữ liệu cứng (Quest, Project, Thể trạng)
     └── [APScheduler]                       <—— Nhắc nhở, check-in cuối ngày
```

### Stack chính
| Layer | Công nghệ |
|---|---|
| Interface | python-telegram-bot 22.8 (tạm thời) |
| Backend | FastAPI + uvicorn |
| Memory Layer | `mem0ai` + `chromadb` (hoặc local vector db) |
| Database | SQLite + SQLModel (ORM) |
| LLM | Google Gemini 3.8 Flash (VLM + Text) |

---

## ❌ Những Gì KHÔNG Làm

- **Reset Database:** Hệ thống có tính năng Hủy diệt Database bằng lệnh `/reset_db`. Yêu cầu nhập mã xác nhận (OTP). CẢNH BÁO: Tính năng này chỉ dùng cho GIAI ĐOẠN PHÁT TRIỂN (Dev Phase) để dọn dẹp dữ liệu rác. Bắt buộc PHẢI XÓA BỎ tính năng này khi dự án release bản Production (Ghi chú này sẽ được theo dõi).
- **Không dùng ConversationHandler / Bấm nút nhiều bước:** Dùng Chat Agentic 100%. User chat -> LLM phân tích -> Dùng Tool cập nhật DB.
- **Không có streak/penalty mechanics** — người dùng không muốn gamification kiểu streak.
- **Không over-engineer** — bắt đầu đơn giản, extend dần.

---

## ✅ Quy tắc làm việc của Agent (BẮT BUỘC)

- **Kiểm tra và Đồng bộ Code:** Luôn luôn chạy `git status` và `git pull origin main` trước khi bắt đầu mỗi session để đảm bảo đang làm việc trên đúng nhánh và có code mới nhất.
- **Giải thích trước khi hành động:** Trong mỗi session, trước khi tiến hành viết code hay chạy lệnh, Agent PHẢI giải thích rõ kế hoạch/logic định làm cho người dùng hiểu.
- **Quản lý Branch:** Bất cứ khi nào làm một TÍNH NĂNG MỚI, LUÔN LUÔN tạo một nhánh mới (`git checkout -b feature/...`), code xong mới push. KHÔNG code tính năng mới trực tiếp trên nhánh `main`.
- **Ghi log đầy đủ:** Ghi vào `PROMPT_HISTORY.md` sau khi hoàn thành tính năng để theo dõi tiến độ.

---

## 💻 Coding Conventions

- Language: **Python 3.11+**
- Async: dùng `async/await` xuyên suốt
- Type hints: bắt buộc trên tất cả function signatures
- Config: dùng `.env` + `pydantic-settings`
- Error handling: không để exception uncaught ở handler level

### ⚠️ Quy tắc ghi file có Unicode (BẮT BUỘC)

**KHÔNG** dùng PowerShell `Set-Content` hay `@'...'@` here-string để ghi file chứa:
- Tiếng Việt (dấu thanh, đặc biệt như â, ê, ơ, ư, ...)
- Emoji (🎯, ⚠️, ✅, ...)

**CÁCH ĐÚNG:** Viết nội dung file bằng Python script `codecs.open(..., 'w', 'utf-8')` rồi gọi chạy script đó, HOẶC dùng tool `replace_file_content` cẩn thận. Python xử lý Unicode đúng — PowerShell thì không.

---

## 📂 Cấu Trúc Thư Mục

```
amazing-nobel/
├── RULES.md                  <- File này — agent đọc mỗi session
├── PROMPT_HISTORY.md         <- Lịch sử prompt — agent đọc mỗi session
├── docker-compose.yml
├── .env.example
├── bot/                      <- Telegram bot handlers (Chỉ đóng vai trò Adapter)
├── api/                      <- FastAPI routes
├── core/                     <- Business logic (brain, memory, scheduler, llm_tools)
├── db/                       <- SQLite models
└── tests/
```

---

*File này được duy trì bởi coding agent. Cập nhật khi có quyết định kiến trúc mới.*
