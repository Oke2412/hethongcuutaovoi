"""bot/main.py -- Entry point for Telegram bot with long polling."""
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config import settings
from db.database import init_db
from core.scheduler import setup_scheduler
from bot.handlers import start, status, chat
from bot.handlers.onboard import build_onboard_handler
from bot.handlers.document import build_document_handler
from bot.handlers.location import build_location_handler
from bot.handlers.quest import build_quest_handler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """Called after the bot is initialised but before polling starts."""
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

    # Commands
    app.add_handler(CommandHandler("start", start.handle))
    app.add_handler(CommandHandler("status", status.handle))
    app.add_handler(build_quest_handler())

    # Conversations (order matters: more specific first)
    app.add_handler(build_onboard_handler())   # /onboard

    # Document upload
    app.add_handler(build_document_handler())

    # Free-text -> LLM (must be last)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat.handle))

    logger.info("Starting bot with long polling...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
