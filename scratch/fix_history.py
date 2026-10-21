# -*- coding: utf-8 -*-
"""Repair the mangled PROMPT_HISTORY entry (PowerShell ate the backticks)."""

import io

PATH = "PROMPT_HISTORY.md"
MARKER = "### [2026-10-20 18:45]"

ENTRY = """
### [2026-10-20 18:45] — Revert Bỏ Loop 3: Ghi Trạng Thái Là Tư Duy, Chỉ Chạy Async Song Song Pass 2
**Agent:** DeepSeek Harness (deepseek-flash)
**Prompt:** "phần bỏ loop 3 revert đi, nó là cần thiết để tư duy, đây là hệ thống về tâm lý nên phải suy nghĩ nên ghi gì, và có thể cho nó ghi async trong lúc đang gọi pass 2 cho đỡ trễ?"
**Kết quả / Quyết định:**
- **Revert toàn bộ việc rút write tools khỏi loop:** `tools=TOOLS_DEF` trở lại; READ_TOOLS / WRITE_TOOL_DEFS / scribe pass / `_WRITE_INTENT_RE` / deferred queue đã xoá sạch. Model vẫn **suy nghĩ** nên ghi gì (đúng yêu cầu hệ tâm lý).
- **Chỉ chuyển phần THI HÀNH sang async:** nếu một lượt loop chỉ phát write tool call (`write_only`), dispatch bằng `asyncio.create_task(_apply_write(...))` rồi break → Pass 2 chạy ngay, writes hoàn tất trong lúc persona đang được viết. Mixed read+write thì vẫn chạy inline như cũ.
- **Flag `DEEPSEEK_DEFER_WRITES`** (mặc định true) bật/tắt; false = hành vi gốc 100% (write chạy inline, loop tiếp tục tới TERMINATE_LOOP) — có test riêng cho cả 2 nhánh.
- **Đo lại cho đúng:** 4.774,6ms của loop 3 là **thời gian LLM quyết định**, không phải thời gian ghi (tool chỉ 0,1ms) → async ghi tiết kiệm ~0,1ms, KHÔNG phải 4,7s. Hai cách thật sự lấy lại 4,7s (overlap lượt suy nghĩ ghi với Pass 2, hoặc cap reasoning) đã ghi trong docs §9 và **không tự ý làm**.
- **Tests:** 4/4 PASS (classification, async dispatch, sequential fallback, SSE frame order).
**Files thay đổi:** core/brain.py, core/llm.py, config.py, tests/test_stream_pipeline.py, docs/SSE_THINKING_STREAMING.md, PROMPT_HISTORY.md
---
"""

src = io.open(PATH, encoding="utf-8").read()
idx = src.find(MARKER)
assert idx != -1, "marker not found"
head = src[:idx]
if not head.endswith("\n\n"):
    head = head.rstrip("\n") + "\n\n"
io.open(PATH, "w", encoding="utf-8", newline="\n").write(head + ENTRY.lstrip("\n"))
print("repaired from index", idx)
