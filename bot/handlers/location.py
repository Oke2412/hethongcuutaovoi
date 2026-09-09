import logging
import asyncio
import h3
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from db.database import AsyncSessionLocal
from core.memory import get_or_create_user

logger = logging.getLogger(__name__)

_location_state: dict[int, dict] = {}
RESOLUTION = 9

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message or update.edited_message
    if not message or not message.location:
        return

    loc = message.location
    lat, lng = loc.latitude, loc.longitude
    tg_user = update.effective_user

    hex_id = h3.latlng_to_cell(lat, lng, RESOLUTION)
    current_state = _location_state.get(tg_user.id)

    if current_state and current_state["hex"] == hex_id:
        return

    # Eagerly update state to prevent race conditions during DB await
    _location_state[tg_user.id] = {
        "hex": hex_id,
        "entered_at": asyncio.get_event_loop().time(),
    }

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_user.id, tg_user.full_name, tg_user.username)
        user_id = user.id

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

async def _process_hex_transition(
    user_id: int, tg_user_id: int,
    old_hex: str | None, new_hex: str,
    lat: float, lng: float, bot,
) -> None:
    from core.neo4j_client import get_neo4j_driver
    from core.llm import evaluate_location_side_quest

    driver = get_neo4j_driver()
    if not driver:
        return

    try:
        async with driver.session() as neo_session:
            await neo_session.run(
                """
                MERGE (h:H3_Cell {hex_id: $hex_id})
                ON CREATE SET h.resolution = $res, h.center_lat = $lat, h.center_lng = $lng,
                              h.visit_count = 1, h.total_dwell_seconds = 0
                ON MATCH SET h.visit_count = h.visit_count + 1
                """,
                hex_id=new_hex, res=RESOLUTION, lat=lat, lng=lng,
            )

            await neo_session.run(
                """
                MATCH (u:User {user_id: $uid}), (h:H3_Cell {hex_id: $hex_id})
                CREATE (u)-[:VISITED {entered_at: datetime(), dwell_seconds: 0}]->(h)
                """,
                uid=str(user_id), hex_id=new_hex,
            )

            adj_hexes = list(h3.grid_disk(new_hex, k=1))
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
            return

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
    except Exception as exc:
        logger.warning(f"Error in hex transition: {exc}")

