"""bot/main.py -- Entry point for Telegram bot with long polling."""
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, TypeHandler, ApplicationHandlerStop

from config import settings
from db.database import init_db
from core.scheduler import setup_scheduler
from bot.handlers import start, status, chat
from bot.handlers.onboard import build_onboard_handler
from bot.handlers.document import build_document_handler
from bot.handlers.location import handle_location
from bot.handlers.quest import build_quest_handlers
from bot.handlers.reset import build_reset_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

async def auth_check(update: Update, context) -> None:
    if settings.allowed_user_id == 0:
        return
    user = update.effective_user
    if user and user.id != settings.allowed_user_id:
        logger.warning(f"Unauthorized access from user {user.id} ({user.full_name})")
        raise ApplicationHandlerStop

async def post_init(application: Application) -> None:
    logger.info("Initialising database...")
    await init_db()

    logger.info("Starting scheduler...")
    scheduler = setup_scheduler(application.bot)
    scheduler.start()

    from bot.ingestion_worker import ingestion_loop
    import asyncio
    asyncio.create_task(ingestion_loop())

    logger.info("Bot ready. Long polling started.")

def main() -> None:
    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .build()
    )

    # Global security filter
    app.add_handler(TypeHandler(Update, auth_check), group=-1)

    app.add_handler(CommandHandler("start", start.handle))
    app.add_handler(CommandHandler("status", status.handle))
    for handler in build_reset_handlers():
        app.add_handler(handler)
    from bot.handlers.quest import build_quest_handlers
    for handler in build_quest_handlers():
        app.add_handler(handler)

    app.add_handler(build_onboard_handler())

    app.add_handler(build_document_handler())

    # Location updates
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE & filters.LOCATION, handle_location))

    # Text messages
    app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, chat.handle))

    logger.info("Starting bot with long polling...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()
