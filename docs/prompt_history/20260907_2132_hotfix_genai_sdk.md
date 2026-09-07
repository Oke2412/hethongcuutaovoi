
### [2026-09-07 21:32] — Hotfix Mem0 Gemini Embedder SDK
**Agent:** Antigravity (Gemini 3.1 Pro)
**Prompt:** ImportError: cannot import name 'genai' from 'google'
**Kết quả / Quyết định:**
- Nhận diện lỗi do thư viện `mem0` sử dụng SDK mới của Google (`google-genai`) cho Embedder, trong khi hệ thống chỉ cài SDK cũ (`google-generativeai`).
- Thêm `google-genai` vào `requirements.txt` để Docker tải về khi Build.
- Đã push lên nhánh `feature/omniscient-event-sidequests`.
**Files thay đổi:** requirements.txt, docs/prompt_history/20260907_2132_hotfix_genai_sdk.md
---
