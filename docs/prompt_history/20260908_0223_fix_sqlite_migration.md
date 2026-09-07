
### [2026-09-08 02:23] — Hotfix: Create SQLite migration script for User table
**Agent:** Antigravity (Gemini 3.1 Pro)
**Prompt:** Lỗi chính của bạn nằm ở dòng này: sqlite3.OperationalError: no such column: user.credits ... giờ làm nào
**Kết quả / Quyết định:**
- Phát hiện lỗi thiếu cột trong database cũ trên server do đã thêm tính năng Credits/Titles vào `User` model nhưng chưa migrate database.
- Đã tạo script `migrate_sqlite.py` bằng Python thuần để tự động `ALTER TABLE` thêm các cột còn thiếu (`credits`, `titles`, `active_buff`, `buff_expires_at`) vào file `data/amazing_nobel.db`.
- Người dùng chỉ cần pull code và chạy script này qua Docker là database sẽ được nâng cấp an toàn mà không bị mất dữ liệu.
- Đã push lên nhánh `feature/omniscient-event-sidequests`.
**Files thay đổi:** migrate_sqlite.py, docs/prompt_history/20260908_0223_fix_sqlite_migration.md
---
