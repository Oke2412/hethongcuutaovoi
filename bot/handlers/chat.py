"""bot/handlers/chat.py -- Free-text message handler -> LLM."""
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
