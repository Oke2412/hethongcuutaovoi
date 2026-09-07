
### [2026-09-07 22:38] — Namespace Conflict Avoidance (google-genai vs google.generativeai)
**Agent:** Antigravity (Gemini 3.1 Pro)
**Prompt:** Sử dụng cái cookbook thì có làm lỗi gì không... ImportError: cannot import name 'genai' from 'google'
**Kết quả / Quyết định:**
- Đã đọc Cookbook và phát hiện thư viện `mem0` yêu cầu SDK mới `google-genai`. Tuy nhiên, mã nguồn cốt lõi của dự án (`core/llm.py`, `core/quest_generator.py`) lại đang sử dụng SDK cũ `google.generativeai`. Việc cài đặt cả hai cùng lúc gây ra xung đột Namespace (Namespace Collision) khiến Python không thể import module `google.genai`.
- Thay vì thực hiện Migration (chuyển đổi) toàn bộ mã nguồn sang SDK mới vốn đòi hỏi viết lại toàn bộ Function Calling (rất rủi ro và tốn kém), tôi đã chọn cách thiết lập cấu hình **Bypass**:
- Chuyển `provider` của Embedder trong `mem0` từ `gemini` sang `litellm`.
- `litellm` tích hợp sẵn việc xử lý Embeddings cho Gemini (dùng `gemini/text-embedding-004`) mà không đòi hỏi phải import gói `google-genai` mới, từ đó tránh hoàn toàn sự xung đột với mã nguồn cũ của chúng ta.
- Đã xóa `google-genai` khỏi `requirements.txt` để trả lại môi trường sạch.
**Files thay đổi:** requirements.txt, core/brain.py, docs/prompt_history/20260907_2238_namespace_conflict.md
---
