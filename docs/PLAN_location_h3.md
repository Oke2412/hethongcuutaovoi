# Plan: H3 Spatial Memory + Telegram Live Location

> **File riêng cho tính năng Location.** Implement sau khi main pipeline refactor xong.

---

## Mục tiêu

Ánh xạ GPS → Ô lục giác H3 → Neo4j node → Phát hiện va chạm nhân quả không gian.  
Khi Master bước vào 1 ô mới có liên kết với sự kiện quá khứ → tự động sinh Side Quest địa điểm.

---

## Dependencies

```
# requirements.txt — thêm vào
h3==4.1.*          # Uber H3 Python binding
neo4j==5.*         # Async Neo4j driver (đã có)
```

---

## 1. Luồng xử lý Live Location

```
Telegram edited_message (Live Location stream)
          │
          ▼
bot/handlers/location.py
          │
          ▼
h3.latlng_to_cell(lat, lng, resolution=9)  → hex_id (chuỗi 15 ký tự)
          │
    ┌─────┴──────┐
    │            │
Same hex?    New hex?
    │            │
    ▼            ▼
Accumulate    Log transition
dwell_time    → Compress trajectory
(no save)     → Check Neo4j for past events
              → Evaluate Side Quest
```

**Resolution 9** (~174m² mỗi ô) — đủ nhỏ để phân biệt "quán cà phê" vs "phòng gym" cùng tòa nhà.

---

## 2. Neo4j Schema cho H3

### Nodes

```cypher
// H3 Cell node
(:H3_Cell {
    hex_id: "8a2a1072c4b7fff",  // H3 index res 9
    resolution: 9,
    center_lat: 10.762,
    center_lng: 106.660,
    label: "Coffee shop Q3",   // Optional — LLM đặt tên sau vài lần visit
    visit_count: 5,
    total_dwell_seconds: 7200
})

// Life event linked to location
(:LifeEvent {
    user_id: "1",
    description: "Gặp mentor tại đây, nhận feedback dự án",
    impact: "HIGH",
    occurred_at: datetime("2026-08-15T14:00:00")
})
```

### Relationships

```cypher
// User visited this hex
(:User)-[:VISITED {
    entered_at: datetime(),
    dwell_seconds: 3600
}]->(:H3_Cell)

// Event happened at this hex
(:LifeEvent)-[:OCCURRED_AT]->(:H3_Cell)

// H3 cells that are neighbors
(:H3_Cell)-[:ADJACENT_TO]->(:H3_Cell)
```

---

## 3. `bot/handlers/location.py` — Rewrite

```python
"""bot/handlers/location.py — Handle Telegram Live Location stream."""
import logging
import asyncio
import h3
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from db.database import AsyncSessionLocal
from core.memory import get_or_create_user

logger = logging.getLogger(__name__)

# In-memory state per user: {user_id: {"hex": "...", "entered_at": datetime, "dwell": 0}}
_location_state: dict[int, dict] = {}

RESOLUTION = 9  # ~174m² per cell

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle both message (first share) and edited_message (live updates)."""
    # Telegram sends live updates via edited_message
    message = update.message or update.edited_message
    if not message or not message.location:
        return

    loc = message.location
    lat, lng = loc.latitude, loc.longitude
    tg_user = update.effective_user

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_user.id, tg_user.full_name, tg_user.username)
        user_id = user.id

    hex_id = h3.latlng_to_cell(lat, lng, RESOLUTION)
    current_state = _location_state.get(user_id)

    if current_state and current_state["hex"] == hex_id:
        # Same hex — just accumulate dwell time, no action needed
        return

    # New hex — process transition
    asyncio.create_task(
        _process_hex_transition(
            user_id=user_id,
            tg_user_id=tg_user.id,
            old_hex=current_state["hex"] if current_state else None,
            new_hex=hex_id,
            lat=lat,
            lng=lng,
            bot=context.bot,
        )
    )

    _location_state[user_id] = {
        "hex": hex_id,
        "entered_at": asyncio.get_event_loop().time(),
    }


async def _process_hex_transition(
    user_id: int, tg_user_id: int,
    old_hex: str | None, new_hex: str,
    lat: float, lng: float, bot,
) -> None:
    """Background: log transition, query Neo4j for past events, maybe generate Side Quest."""
    from core.neo4j_client import get_neo4j_driver
    from core.llm import evaluate_location_side_quest

    driver = get_neo4j_driver()
    if not driver:
        return

    async with driver.session() as neo_session:
        # 1. Upsert H3_Cell node
        await neo_session.run(
            """
            MERGE (h:H3_Cell {hex_id: $hex_id})
            ON CREATE SET h.resolution = $res, h.center_lat = $lat, h.center_lng = $lng,
                          h.visit_count = 1, h.total_dwell_seconds = 0
            ON MATCH SET h.visit_count = h.visit_count + 1
            """,
            hex_id=new_hex, res=RESOLUTION, lat=lat, lng=lng,
        )

        # 2. Log VISITED relationship
        await neo_session.run(
            """
            MATCH (u:User {user_id: $uid}), (h:H3_Cell {hex_id: $hex_id})
            CREATE (u)-[:VISITED {entered_at: datetime(), dwell_seconds: 0}]->(h)
            """,
            uid=str(user_id), hex_id=new_hex,
        )

        # 3. Query past events at this hex (or adjacent hexes)
        adj_hexes = list(h3.grid_disk(new_hex, k=1))  # Current + 6 neighbors
        result = await neo_session.run(
            """
            MATCH (e:LifeEvent)-[:OCCURRED_AT]->(h:H3_Cell)
            WHERE h.hex_id IN $hexes AND e.user_id = $uid
            RETURN e.description AS desc, e.impact AS impact, e.occurred_at AS ts
            ORDER BY e.occurred_at DESC LIMIT 3
            """,
            hexes=adj_hexes, uid=str(user_id),
        )
        past_events = [dict(r) for r in await result.data()]

    if not past_events:
        return  # No relevant history — silent

    # 4. Evaluate if side quest is warranted
    side_quest_text = await evaluate_location_side_quest(
        user_id=user_id,
        hex_id=new_hex,
        past_events=past_events,
    )

    if side_quest_text:
        await bot.send_message(
            chat_id=tg_user_id,
            text=side_quest_text,
            parse_mode="Markdown",
        )
```

---

## 4. `core/neo4j_client.py` — Singleton Driver [NEW]

```python
"""core/neo4j_client.py — Neo4j async driver singleton."""
import logging
from neo4j import AsyncGraphDatabase
from config import settings

logger = logging.getLogger(__name__)
_driver = None

def get_neo4j_driver():
    global _driver
    if _driver is None:
        try:
            _driver = AsyncGraphDatabase.driver(
                getattr(settings, "neo4j_uri", "neo4j://neo4j:7687"),
                auth=(
                    getattr(settings, "neo4j_user", "neo4j"),
                    getattr(settings, "neo4j_password", "password"),
                ),
            )
        except Exception as exc:
            logger.warning("Neo4j unavailable: %s", exc)
            return None
    return _driver
```

---

## 5. `core/llm.py` — `evaluate_location_side_quest()`

```python
async def evaluate_location_side_quest(
    user_id: int, hex_id: str, past_events: list[dict]
) -> str:
    """Use gemini-3.8-flash to evaluate if location warrants a Side Quest."""
    from core.omniscience import get_mini_context
    client = _get_gemini_client()
    mini_ctx = await get_mini_context(user_id)

    events_text = "\n".join(
        f"- [{e['ts']}] {e['desc']} (impact: {e['impact']})"
        for e in past_events
    )

    prompt = (
        f"[TRANG THAI HIEN TAI]\n{mini_ctx}\n\n"
        f"[O H3 HIEN TAI: {hex_id}]\n"
        f"[SU KIEN QUA KHU TAI/GAN DAY]\n{events_text}\n\n"
        "Nhiem vu: Danh gia xem co nen sinh Side Quest khong.\n"
        "- Neu khong: chi output 'NO'\n"
        "- Neu co: output noi dung Side Quest (giong Raphael, lanh lung, co thuong/phat ro rang, max 3 dong)"
    )

    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=MODEL_DEEP,  # gemini-3.8-flash
            contents=prompt,
        )
        text = response.text.strip()
        return "" if text.upper().startswith("NO") else text
    except Exception as exc:
        logger.warning("Location side quest generation failed: %s", exc)
        return ""
```

---

## 6. `bot/main.py` — Register location handler

```python
# Thêm vào setup handlers
from bot.handlers.location import handle_location
from telegram.ext import MessageHandler, filters

# Cần handle cả message (lần đầu share) và edited_message (live updates)
app.add_handler(MessageHandler(filters.LOCATION, handle_location))
app.add_handler(MessageHandler(
    filters.UpdateType.EDITED_MESSAGE & filters.LOCATION,
    handle_location
))
```

---

## 7. Neo4j Indexes (chạy 1 lần khi start)

```cypher
CREATE INDEX h3_hex_id IF NOT EXISTS FOR (h:H3_Cell) ON (h.hex_id);
CREATE INDEX life_event_uid IF NOT EXISTS FOR (e:LifeEvent) ON (e.user_id);
CREATE INDEX user_uid IF NOT EXISTS FOR (u:User) ON (u.user_id);
```

Tạo trong `db/database.py` hoặc script riêng `scripts/init_neo4j.py`.

---

## 8. Config additions — `.env` + `config.py`

```bash
# .env
NEO4J_URI=neo4j://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
H3_RESOLUTION=9
```

```python
# config.py — thêm vào Settings
neo4j_uri: str = "neo4j://neo4j:7687"
neo4j_user: str = "neo4j"
neo4j_password: str = "password"
h3_resolution: int = 9
```

---

## Files Summary

| File | Action |
|---|---|
| `bot/handlers/location.py` | **[REWRITE]** — H3 transition detection, async Neo4j write |
| `core/neo4j_client.py` | **[NEW]** — Singleton driver |
| `core/llm.py` | **[ADD]** — `evaluate_location_side_quest()` |
| `bot/main.py` | **[UPDATE]** — Register edited_message location handler |
| `scripts/init_neo4j.py` | **[NEW]** — Index creation script |
| `requirements.txt` | **[ADD]** — `h3==4.1.*` |
| `.env.example` | **[ADD]** — Neo4j + H3 config vars |

---

## Verification

```bash
# Test H3 import
python -c "import h3; print(h3.latlng_to_cell(10.762, 106.660, 9))"
# Expected: 8-character hex string like "89283082837ffff"

# Test Neo4j connection
python -c "
import asyncio
from neo4j import AsyncGraphDatabase
async def test():
    d = AsyncGraphDatabase.driver('neo4j://localhost:7687', auth=('neo4j','password'))
    async with d.session() as s:
        r = await s.run('RETURN 1 AS n')
        print(await r.single())
asyncio.run(test())
"
```
