
### [2026-09-08 00:45] — Hotfix: Change Mem0 LLM Provider to Gemini
**Agent:** Antigravity (Gemini 3.1 Pro)
**Prompt:** ModuleNotFoundError: No module named 'litellm'
**Kết quả / Quyết định:**
- Phát hiện `mem0` mặc định sử dụng `litellm` làm LLM provider nhưng thư viện này chưa được cài đặt.
- Thay vì thêm `litellm` vào `requirements.txt` (sẽ khiến Docker phải build lại mất ~17 phút), quyết định đổi `provider` của LLM trong `mem0` thành `"gemini"` để tận dụng luôn thư viện `google-genai` vừa cài đặt ở bước trước.
- Đổi `"model": "gemini/gemini-3.8-flash"` thành `"model": "gemini-3.8-flash"` cho tương thích với provider mới.
- Đã push lên nhánh `feature/omniscient-event-sidequests`.
**Files thay đổi:** core/brain.py, docs/prompt_history/20260908_0045_fix_mem0_llm_provider.md
---
