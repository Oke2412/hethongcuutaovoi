
### [2026-09-08 10:35] — Hotfix: Sửa lỗi thiếu ID trong FunctionResponse của SDK google-genai
**Agent:** Antigravity
**Lỗi gặp phải:** `google.genai.errors.ClientError: 400 INVALID_ARGUMENT. Function call is missing a thought_signature in functionCall parts...`
**Nguyên nhân:** Khi gọi Tool thủ công bằng SDK `google-genai` mới, hàm helper `Part.from_function_response()` không hỗ trợ truyền tham số `id`. Do đó, khi phản hồi lại cho LLM (`chat.send_message`), backend của Google không thể map được Tool Response với Tool Call tương ứng trong lịch sử chat, dẫn đến văng lỗi `thought_signature` (bởi model Gemini mới mặc định yêu cầu format chặt chẽ).
**Cách giải quyết:**
- Xóa bỏ việc dùng hàm helper `from_function_response`.
- Tự khởi tạo class `types.Part(function_response=types.FunctionResponse(name=fc.name, id=fc.id, response=...))` để ép truyền `id` của function call trả về.
- Giải thích lỗi 503 cho user là do máy chủ Gemini quá tải tạm thời.
**Files thay đổi:** core/llm.py, docs/prompt_history/20260908_1035_fix_functioncall_id.md
