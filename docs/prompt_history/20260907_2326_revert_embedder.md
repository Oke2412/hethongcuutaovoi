
### [2026-09-07 23:26] — Revert Unsupported Embedder Config
**Agent:** Antigravity (Gemini 3.1 Pro)
**Prompt:** Value error, Unsupported embedding provider: litellm
**Kết quả / Quyết định:**
- Phát hiện cấu hình Embedder bị đổi thành `litellm` gây lỗi `Unsupported embedding provider` trong `mem0`.
- Khôi phục cấu hình về `"provider": "gemini"` và `"model": "models/text-embedding-004"` để sử dụng native SDK (đã cài đặt `google-genai` ở bước trước).
- Đã push lên nhánh `feature/omniscient-event-sidequests`.
**Files thay đổi:** core/brain.py, docs/prompt_history/20260907_2326_revert_embedder.md
---
