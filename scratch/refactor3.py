import codecs

def write_utf8(path, content):
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(content)

# 1. bot/handlers/location.py
loc_content = """import logging
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

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_user.id, tg_user.full_name, tg_user.username)
        user_id = user.id

    hex_id = h3.latlng_to_cell(lat, lng, RESOLUTION)
    current_state = _location_state.get(user_id)

    if current_state and current_state["hex"] == hex_id:
        return

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
    from core.neo4j_client import get_neo4j_driver
    from core.llm import evaluate_location_side_quest

    driver = get_neo4j_driver()
    if not driver:
        return

    try:
        async with driver.session() as neo_session:
            await neo_session.run(
                \"\"\"
                MERGE (h:H3_Cell {hex_id: $hex_id})
                ON CREATE SET h.resolution = $res, h.center_lat = $lat, h.center_lng = $lng,
                              h.visit_count = 1, h.total_dwell_seconds = 0
                ON MATCH SET h.visit_count = h.visit_count + 1
                \"\"\",
                hex_id=new_hex, res=RESOLUTION, lat=lat, lng=lng,
            )

            await neo_session.run(
                \"\"\"
                MATCH (u:User {user_id: $uid}), (h:H3_Cell {hex_id: $hex_id})
                CREATE (u)-[:VISITED {entered_at: datetime(), dwell_seconds: 0}]->(h)
                \"\"\",
                uid=str(user_id), hex_id=new_hex,
            )

            adj_hexes = list(h3.grid_disk(new_hex, k=1))
            result = await neo_session.run(
                \"\"\"
                MATCH (e:LifeEvent)-[:OCCURRED_AT]->(h:H3_Cell)
                WHERE h.hex_id IN $hexes AND e.user_id = $uid
                RETURN e.description AS desc, e.impact AS impact, e.occurred_at AS ts
                ORDER BY e.occurred_at DESC LIMIT 3
                \"\"\",
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

"""
write_utf8(r'c:\Users\Asus\Documents\antigravity\amazing-nobel\bot\handlers\location.py', loc_content)

# 2. Update bot/handlers/chat.py
chat_content = """\"\"\"bot/handlers/chat.py -- Free-text message handler -> LLM.\"\"\"
import logging
from telegram import Update
from telegram.ext import ContextTypes
from db.database import AsyncSessionLocal
from core.memory import get_or_create_user
from core.brain import brain

logger = logging.getLogger(__name__)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    message = update.message
    if tg_user is None or message is None or not message.text:
        return
    await message.chat.send_action("typing")
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session, tg_user.id, tg_user.full_name, tg_user.username
        )
        
    response, keyboard = await brain.process_input(user_id=str(user.id), text_content=message.text)
    
    if keyboard:
        await message.reply_text(response, reply_markup=keyboard)
    else:
        await message.reply_text(response)
"""
write_utf8(r'c:\Users\Asus\Documents\antigravity\amazing-nobel\bot\handlers\chat.py', chat_content)

# 3. Update bot/handlers/document.py
doc_content = """\"\"\"bot/handlers/document.py -- Handle document uploads (.txt, .md).\"\"\"
import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from db.database import AsyncSessionLocal
from core.memory import get_or_create_user
from core.brain import brain

logger = logging.getLogger(__name__)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message or not message.document:
        return

    doc = message.document
    filename = doc.file_name.lower() if doc.file_name else ""
    
    if not (filename.endswith('.txt') or filename.endswith('.md')):
        await message.reply_text("⚠️ Hiện tại tôi chỉ hỗ trợ phân tích file .txt hoặc .md.")
        return

    if doc.file_size and doc.file_size > 5 * 1024 * 1024:
        await message.reply_text("⚠️ File quá lớn. Vui lòng gửi file dưới 5MB.")
        return

    status_msg = await message.reply_text("⏳ Đang nạp tài liệu vào bộ não AI. Vui lòng chờ...")

    try:
        tg_file = await context.bot.get_file(doc.file_id)
        byte_array = await tg_file.download_as_bytearray()
        
        content = byte_array.decode('utf-8', errors='replace')
        
        if len(content.strip()) == 0:
            await status_msg.edit_text("⚠️ File trống.")
            return

        tg_user = update.effective_user
        async with AsyncSessionLocal() as session:
            user = await get_or_create_user(session, tg_user.id, tg_user.full_name, tg_user.username)
            
        filename_safe = doc.file_name or "file"
        prompt = (
            "[TAI LIEU DINH KEM: " + filename_safe + "]\\n"
            + content
        )

        response, keyboard = await brain.process_input(user_id=str(user.id), text_content=prompt)

        if keyboard:
            await status_msg.edit_text(response, reply_markup=keyboard)
        else:
            await status_msg.edit_text(response)

    except Exception as exc:
        logger.error(f"Error handling document: {exc}", exc_info=True)
        await status_msg.edit_text("⚠️ Đã xảy ra lỗi trong quá trình phân tích file.")

def build_document_handler() -> MessageHandler:
    return MessageHandler(filters.Document.ALL, handle_document)
"""
write_utf8(r'c:\Users\Asus\Documents\antigravity\amazing-nobel\bot\handlers\document.py', doc_content)

# 4. Update bot/main.py
main_content = """\"\"\"bot/main.py -- Entry point for Telegram bot with long polling.\"\"\"
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config import settings
from db.database import init_db
from core.scheduler import setup_scheduler
from bot.handlers import start, status, chat
from bot.handlers.onboard import build_onboard_handler
from bot.handlers.document import build_document_handler
from bot.handlers.location import handle_location
from bot.handlers.quest import build_quest_handler
from bot.handlers.reset import build_reset_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

async def post_init(application: Application) -> None:
    logger.info("Initialising database...")
    await init_db()

    logger.info("Starting scheduler...")
    scheduler = setup_scheduler(application.bot)
    scheduler.start()

    logger.info("Bot ready. Long polling started.")

def main() -> None:
    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start.handle))
    app.add_handler(CommandHandler("status", status.handle))
    for handler in build_reset_handlers():
        app.add_handler(handler)
    app.add_handler(build_quest_handler())

    app.add_handler(build_onboard_handler())

    app.add_handler(build_document_handler())

    # Location updates
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE & filters.LOCATION, handle_location))

    # Text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat.handle))

    logger.info("Starting bot with long polling...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()
"""
write_utf8(r'c:\Users\Asus\Documents\antigravity\amazing-nobel\bot\main.py', main_content)

# 5. Add AGENTS.md
agents_content = """# Raphael Life OS — Agent Rules

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
"""
write_utf8(r'c:\Users\Asus\Documents\antigravity\amazing-nobel\AGENTS.md', agents_content)

print("Batch 3 created successfully.")
