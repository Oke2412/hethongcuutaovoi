
### [2026-09-07 20:48] — Hotfix Mem0 Embedder Provider
**Agent:** Antigravity (Gemini 3.1 Pro)
**Prompt:** Mem0 crashing due to Missing OpenAI credentials / Unsupported embedding provider
**Kết quả / Quyết định:**
- Phát hiện lỗi `mem0` tự động gọi OpenAI Embedder vì thiếu cấu hình Embedding Provider.
- Thêm cấu hình `"embedder": {"provider": "gemini", "config": {"model": "models/text-embedding-004"}}` vào `core/brain.py` để ép Mem0 sử dụng API Key của Gemini thay vì OpenAI.
- Đã sửa tên provider từ `google_genai` thành `gemini` để tương thích với phiên bản `mem0` hiện tại.
- Đã push lên nhánh `feature/omniscient-event-sidequests`.
**Files thay đổi:** core/brain.py, docs/prompt_history/20260907_2048_hotfix_embedder.md
---
