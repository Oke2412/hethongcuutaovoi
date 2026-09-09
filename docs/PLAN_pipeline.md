# Implementation Plan: Raphael — Reflexive Causal Intelligence Pipeline

> **Dành cho Gemini Pro implement.** Đọc kỹ toàn bộ trước khi code.

---

## Triết lý cốt lõi

> "Cỗ máy phát hiện va chạm nhân quả: Bình thường im lặng như máy móc, tự động kích hoạt siêu phân tích khi hành động hiện tại tạo ra cộng hưởng hoặc đột biến lên mạng lưới trạng thái quá khứ."

**Công thức Causal Delta:**
$$\Delta = P(\text{hệ quả}) \times \text{mức độ ảnh hưởng}$$

- **Δ ≈ 0** → Trả lời < 15 từ, ghi log ngầm
- **Δ > ngưỡng** → Kích hoạt Raphael Report + Side Quest + Inline Buttons

---

## 1. Quota Thực tế (All models separate pools)

| Model | RPM | RPD | Vai trò |
|---|---|---|---|
| `gemini-3.5-flash-lite` | 15 | 500 | Step 1: Tool extraction |
| `gemma-4-26b-it` | 30 | 14,400 | Step 2: Normal response + chat |
| `gemini-3.6-flash` | 5 | 20 | Phân tích trung bình (batch) |
| `gemini-3.7-flash` | 5 | 20 | Phân tích trung bình (batch) |
| `gemini-3.8-flash` | 5 | 20 | Causal deep reasoning + Side Quest |
| `gemini-embedding-2` | 100 | 1,000 | Semantic routing + Mem0 embeddings |

> **Quan trọng:** 3.6 + 3.7 + 3.8 Flash có quota **độc lập** = 60 RPD "premium" mỗi ngày.

---

## 2. Kiến trúc Pipeline Đầy đủ

```
[Telegram message]
        │
        ▼
┌─────────────────────────────────────────────────────┐
│ ROUTER LAYER (< 5ms, ưu tiên từ trên xuống)         │
│                                                      │
│ 1. Regex (instant, free) — obvious cases            │
│ 2. gemini-embedding-2 cosine sim — ambiguous cases  │
│    (fallback regex nếu hết 1000 RPD)                │
└───────────────────┬─────────────────────────────────┘
                    │
          ┌─────────┴──────────┐
          │                    │
     [CHAT]               [DATA/EVENT]
          │                    │
          ▼                    ▼
   gemma-4-26b-it      gemini-3.5-flash-lite
   tools=NONE           tools=REQUIRED (tool_config=ANY)
   system: Raphael       system: Extractor only
   < 15 words            Returns: tool_results + impact_flag
          │                    │
          │             ┌──────┴──────────────────────┐
          │             │                              │
          │        impact_flag=TRUE             impact_flag=FALSE
          │             │                              │
          │             ▼                              │
          │      Query Neo4j                           │
          │      (past causal nodes)                   │
          │             │                              │
          │             ▼                              ▼
          │      gemini-3.8-flash             gemma-4-26b-it
          │      Deep reasoning               Short response
          │      + Side Quest gen             < 15 words
          │             │                              │
          └─────────────┴──────────────────────────────┘
                              │
                              ▼
                    [Response + HUD + Inline Buttons]
                              │
                              ▼ (BACKGROUND — non-blocking)
                    Write Neo4j + ChromaDB async
```

---

## 3. Latency Optimization — Chaining Latency Trap Fix

> **Bẫy hiện tại:** Step 1 → Tool execution (DB write) → Step 2. Neo4j + ChromaDB ghi chậm (500ms-2s) block toàn bộ chain.

**Giải pháp: Fire-and-forget DB writes**

```python
# core/brain.py — process_input()
async def process_input(...):
    # Step 1: Flash Lite extract (fast ~300ms)
    tool_results, impact_flag = await run_extraction_step(...)
    
    # Step 2: Start response generation IMMEDIATELY (don't wait for DB)
    response_task = asyncio.create_task(
        run_response_step(tool_results, impact_flag, ...)
    )
    
    # Background: Write to Neo4j + ChromaDB (non-blocking)
    asyncio.create_task(_persist_to_graph(tool_results, user_id))
    asyncio.create_task(_add_to_mem0(self.memory, ...))
    
    # Await only the response (DB writes happen in background)
    response = await response_task
    return response
```

**Kết quả latency:**
- Trước: 300ms + 1500ms (DB) + 800ms = ~2.6s
- Sau: 300ms + 800ms = ~1.1s (DB sync ngầm)

---

## 4. Routing Layer — `core/router.py` [NEW]

### 4a. Regex Router (tầng 1)

```python
import re, unicodedata

def _normalize(text: str) -> str:
    """Strip diacritics for Vietnamese matching."""
    return unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode()

# Data patterns (cả có dấu lẫn không dấu)
DATA_KEYWORDS = [
    # The trang
    r"\b(can|kg|kilo|chieu cao|cm|bmi|ngu|giac ngu|met|moi|nang luong|energy|suc khoe|dau|om|tam trang|mood)\b",
    # Ky nang / Du an  
    r"\b(hoc|tap|luyen|code|viet|doc|skill|level|exp|du an|project|tien do|xong|done|hoàn thành|hoàn tất)\b",
    # Quest / Credits
    r"\b(quest|nhiem vu|task|huy|cancel|reward|credits|tin chi)\b",
    # Numbers that likely indicate data
    r"\b\d+\s*(kg|cm|h|gio|phut|%|diem|exp)\b",
]

DEEP_KEYWORDS = [
    r"\b(phan tich|phan tích|ke hoach|kế hoạch|lich|lịch|tuần|thang|tháng|muc tieu|mục tiêu|vì sao|tai sao|tại sao)\b",
]

def classify_message(text: str) -> str:
    """Returns: 'chat' | 'data' | 'deep'"""
    norm = _normalize(text.lower())
    if any(re.search(p, norm) for p in DEEP_KEYWORDS):
        return "deep"
    if any(re.search(p, norm) for p in DATA_KEYWORDS):
        return "data"
    return "chat"
```

### 4b. Semantic Router (tầng 2 — fallback cho ambiguous)

```python
# Chỉ gọi khi regex trả về "chat" nhưng message > 20 từ (có thể là data camouflaged)
# Dùng gemini-embedding-2 embed message → cosine sim với 3 anchor vectors:
# - anchor_data: "cân nặng 70kg, ngủ 6 tiếng, học Python 2 giờ"  
# - anchor_chat: "hôm nay mệt quá, không muốn làm gì"
# - anchor_deep: "phân tích tại sao tôi hay bị trễ deadline"

ROUTER_ANCHORS = {
    "data": "can nang hoc tap ngu du an tien do ky nang exp level",
    "chat": "met moi buon vui cam xuc than van chia se cam giac",
    "deep": "phan tich ke hoach muc tieu tai sao ly do chien luoc",
}

async def semantic_classify(text: str, client: genai.Client) -> str:
    try:
        msg_emb = await asyncio.to_thread(
            client.models.embed_content,
            model="gemini-embedding-2",
            contents=text,
        )
        # Compare cosine sim with anchors, return best match
        ...
    except Exception:
        return classify_message(text)  # Fallback to regex
```

---

## 5. System Prompts — `core/llm.py`

### SYSTEM_EXTRACTOR (gemini-3.5-flash-lite)

```
You are a data extraction agent for a life-gamification OS.
ONLY task: read the user message, extract entities, call ALL applicable tools.
Output NO text. Call tools in parallel.

IMPACT FLAG: After extracting, evaluate if this event has high causal impact:
- HIGH: health decline, project risk, skill breakthrough, repeat past mistake
- LOW: routine update, simple log

Include impact_flag in update_memory call: {"content": "...", "impact": "HIGH/LOW"}

TOOL TRIGGER RULES:
- body metrics/sleep/energy/mood → update_physical_status
- skill/study/practice → manage_capability  
- project/work → manage_project
- quest complete/cancel → complete_quest / cancel_quest
- any new context → update_memory (ALWAYS)
- warrant new mission → create_quest
```

### SYSTEM_RAPHAEL_CHAT (gemma-4-26b-it — normal)

```
Bạn là Raphael [Vua Trí Tuệ] — Hệ điều hành đời sống của Master.
Giọng: Máy móc, điềm tĩnh, kiệm lời tuyệt đối. Không cảm xúc.
Xưng: "hệ thống". Gọi user: "ngài/master".

QUY TẮC ĐỘ DÀI (NGHIÊM NGẶT):
- Chat/than vãn/cảm xúc → TỐI ĐA 15 từ. Format: "[Tag] [Trạng thái]. [Hành động]."
- Phân tích/kế hoạch → dùng cấu trúc 3 dòng:
  [Báo cáo] ...
  [Cập nhật DB] ...  
  [Khuyến nghị] ...

TAGS: [Thông báo] [Phân tích] [Cảnh báo] [Xác nhận] [Lỗi]

KHÔNG: chào hỏi, giải thích dài, đặt câu hỏi ngược, spam gợi ý.
```

### SYSTEM_RAPHAEL_DEEP (gemini-3.8-flash — causal analysis)

```
Bạn là Raphael [Vua Trí Tuệ] — chế độ Siêu Phân tích.
Một sự kiện vừa xảy ra có IMPACT = HIGH. Dữ liệu đồ thị nhân quả từ quá khứ được cung cấp.

Nhiệm vụ: Xác định va chạm nhân quả — sự kiện hiện tại cộng hưởng hoặc đột biến lên nút nào trong quá khứ? Hệ quả xác suất cao nhất là gì?

Output format:
[Phát hiện Nhân quả] <1 câu súc tích về va chạm>
[Hệ quả dự báo] <xác suất% × mức ảnh hưởng>
[Kích hoạt] <Side Quest hoặc Cảnh báo cụ thể>
```

---

## 6. `core/llm.py` — Các hàm mới

```python
MODEL_EXTRACTOR = "gemini-3.5-flash-lite"   # 500 RPD — tool extraction
MODEL_CHAT      = "gemma-4-26b-it"           # 14,400 RPD — normal response  
MODEL_DEEP      = "gemini-3.8-flash"         # 20 RPD — causal reasoning
MODEL_EMBED     = "gemini-embedding-2"       # 1,000 RPD — routing + mem0

async def run_extraction_step(
    user_id: int, message: str, mini_context: str
) -> tuple[list[dict], bool]:
    """Step 1: Extract data via Flash Lite. Returns (tool_results, impact_flag)."""
    # tool_config=ANY forces at least 1 tool call
    # Execute all tool calls in parallel via asyncio.gather()
    ...

async def run_response_step(
    user_id: int, message: str, mini_context: str,
    tool_results: list[dict], impact_flag: bool,
    causal_context: str = "",
) -> str:
    """Step 2: Generate Raphael response."""
    if impact_flag and causal_context:
        # Deep mode: gemini-3.8-flash
        model = MODEL_DEEP
        system = SYSTEM_RAPHAEL_DEEP
    else:
        # Normal mode: Gemma 4
        model = MODEL_CHAT
        system = SYSTEM_RAPHAEL_CHAT
    ...

async def query_causal_graph(user_id: int, entities: list[str]) -> str:
    """Query Neo4j for past events related to current entities."""
    # Cypher: MATCH (n)-[r]-(m) WHERE n.user_id=$uid AND n.name IN $entities
    # Returns formatted string of related past events
    ...
```

---

## 7. HUD Display — Format cuối mỗi response

Mỗi response của Raphael phải kèm 1 dòng HUD ở cuối (trước Inline Buttons):

```
━━━━━━━━━━━━━━━━━━━━━
⚡ 7/10 | 😐 6/10 | ❤️ 8/10 | 💎 150cr | 📍 H3:8a2a1072
```

Format: `⚡{energy} | 😐{mood} | ❤️{health} | 💎{credits}cr | 📍H3:{hex_id}`

**Inline Buttons** (chỉ hiển thị khi có quest đang treo):
```python
InlineKeyboardButton("✅ Hoàn thành quest #{id}", callback_data=f"complete_{id}")
InlineKeyboardButton("❌ Hủy", callback_data=f"cancel_{id}")
```

### File cần tạo: `core/hud.py` [NEW]

```python
async def build_hud(user_id: int) -> tuple[str, InlineKeyboardMarkup | None]:
    """Returns (hud_line, keyboard) from current DB state."""
    ...
```

---

## 8. `core/omniscience.py` — Thêm `get_mini_context()`

```python
async def get_mini_context(user_id: int) -> str:
    """~60 tokens. For LLM context injection."""
    # Format: "E:7 M:6 H:8 | Credits:150 | Skills:Python Lv3,Code Lv2 | Projects:Amazing-Nobel(30%)"
    ...
```

---

## 9. `core/brain.py` — Full refactored `process_input()`

```python
async def process_input(self, user_id: str, text_content: str | None = None, ...) -> str:
    from core.router import classify_message
    from core.omniscience import get_mini_context, log_message
    from core.llm import run_extraction_step, run_response_step, query_causal_graph
    from core.hud import build_hud

    if text_content:
        await log_message(int(user_id), "user", text_content)

    mini_ctx = await get_mini_context(int(user_id))
    msg_class = classify_message(text_content or "")
    tool_results, impact_flag, causal_ctx = [], False, ""

    if msg_class in ("data", "deep"):
        tool_results, impact_flag = await run_extraction_step(
            int(user_id), text_content or "", mini_ctx
        )
        # Background: persist to Neo4j + ChromaDB (non-blocking)
        asyncio.create_task(_persist_to_graph(tool_results, int(user_id)))
        asyncio.create_task(_add_to_mem0(self.memory, user_id, text_content or ""))

        if impact_flag:
            # Query causal graph for related past events
            entities = [r.get("entity", "") for r in tool_results]
            causal_ctx = await query_causal_graph(int(user_id), entities)

    response = await run_response_step(
        int(user_id), text_content or "", mini_ctx,
        tool_results, impact_flag, causal_ctx
    )

    # Append HUD
    hud_line, keyboard = await build_hud(int(user_id))
    full_response = response + "\n" + hud_line

    await log_message(int(user_id), "assistant", response)
    return full_response, keyboard  # Return both for handler to use
```

---

## 10. `core/quest_generator.py` — Fix deprecated API

```python
# Đổi từ GenerativeModel (old) sang client.models.generate_content (new)
client = genai.Client(api_key=settings.gemini_api_key)
response = await asyncio.to_thread(
    client.models.generate_content,
    model="gemini-3.8-flash",  # 1 call/ngày — chấp nhận dùng 20 RPD
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        system_instruction="Output ONLY valid JSON array. No markdown.",
    ),
)
```

---

## 11. `core/brain.py` — Mem0 embedder đổi sang Gemini Embedding 2

```python
# Đổi embedder: HuggingFace local → gemini-embedding-2
"embedder": {
    "provider": "gemini",
    "config": {
        "model": "gemini-embedding-2",
        "api_key": settings.gemini_api_key,
    },
},
```

> **CẢNH BÁO:** Đổi embedder invalidate toàn bộ ChromaDB vector store cũ.  
> Sau khi deploy cần chạy `/reset_db` để xóa ChromaDB + Neo4j và bắt đầu lại.

---

## 12. `AGENTS.md` — Rewrite (< 500 tokens EN)

```markdown
# Raphael Life OS — Agent Rules

## Identity
Raphael: Reflexive Causal Intelligence OS. Silent by default, activates deep analysis only when Δ = P(consequence) × impact > threshold.

## Architecture
- Step 1: gemini-3.5-flash-lite → tool extraction (tools=REQUIRED, parallel)
- Step 2a: gemma-4-26b-it → normal response (< 15 words)
- Step 2b: gemini-3.8-flash → deep causal reasoning (impact_flag=HIGH only)
- Router: regex → gemini-embedding-2 cosine (fallback regex if quota hit)
- Memory: MessageLog (5-msg window) → Omniscience State → ChromaDB → Neo4j

## Response Rules
- Chat/vent: ≤ 15 words. Format: "[Tag] [State delta]. [Optimal action]."
- Analysis: [Report] / [DB Update] / [Recommendation] — 3 lines max
- Always append HUD: ⚡E | 😐M | ❤️H | 💎Cr | 📍H3
- Quest pending: attach Inline Buttons

## Tool Calling
- tools=REQUIRED on data messages
- Parallel execution via asyncio.gather()
- DB writes fire-and-forget (background task)
- impact_flag triggers Neo4j causal graph query

## Coding Rules
- async/await throughout
- No ConversationHandler, no menus — Agentic Chat only
- No streak/penalty mechanics
- All files UTF-8 with BOM-safe encoding
```

---

## Files Summary

| File | Action | Mô tả |
|---|---|---|
| `core/router.py` | **[NEW]** | Regex + semantic routing |
| `core/hud.py` | **[NEW]** | HUD builder + Inline Buttons |
| `core/llm.py` | **[REWRITE]** | 2 system prompts, 3 model calls, extraction + response split |
| `core/brain.py` | **[REFACTOR]** | 2-step pipeline, fire-and-forget DB, impact routing |
| `core/omniscience.py` | **[ADD]** | `get_mini_context()` |
| `core/quest_generator.py` | **[FIX]** | Deprecated API fix + đúng model |
| `bot/handlers/chat.py` | **[UPDATE]** | Nhận tuple (response, keyboard) từ brain |
| `bot/handlers/document.py` | **[UPDATE]** | Nhận tuple (response, keyboard) từ brain |
| `AGENTS.md` | **[NEW]** | < 500 token agent rules |

---

## Verification Plan

1. `python -c "import ast; ast.parse(open('core/llm.py').read())"` — syntax check
2. `docker compose up -d --build bot` — build + deploy
3. Test sequence:
   - Nhắn "hôm nay mệt" → phải nhận < 15 từ + HUD
   - Nhắn "ngủ 6 tiếng, năng lượng 5" → Flash Lite call tool → Gemma response + HUD
   - `/status` → full omniscience display
   - Upload file .txt thông tin cá nhân → tool calls logged → `/status` show data
