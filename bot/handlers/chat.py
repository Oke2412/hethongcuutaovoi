"""bot/handlers/chat.py -- Free-text message handler -> LLM."""
import logging
import asyncio
from collections import defaultdict
from telegram import Update
from telegram.ext import ContextTypes
from db.database import AsyncSessionLocal
from core.memory import get_or_create_user
from core.brain import brain

logger = logging.getLogger(__name__)

# --- DEBOUNCE STATE ---
_pending_messages = defaultdict(list)
_pending_images = {}
_debounce_tasks = {}
DEBOUNCE_DELAY = 5.0  # seconds

async def _process_after_delay(tg_user, update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await asyncio.sleep(DEBOUNCE_DELAY)
    except asyncio.CancelledError:
        # A new message came in, timer is reset
        return

    # 5 seconds passed. Grab all buffered data.
    user_id = tg_user.id
    texts = _pending_messages.pop(user_id, [])
    image_bytes = _pending_images.pop(user_id, None)
    
    if not texts and not image_bytes:
        return
        
    combined_text = "\n".join(texts)
    
    try:
        try:
            await update.message.chat.send_action("typing")
        except Exception as e:
            logger.warning(f"Network transient error ignored during send_action: {e}")
        async with AsyncSessionLocal() as session:
            user = await get_or_create_user(
                session, tg_user.id, tg_user.full_name, tg_user.username
            )
            
        response, keyboard = await brain.process_input(
            user_id=str(user.id), 
            text_content=combined_text, 
            image_bytes=image_bytes
        )
        
        from telegram import ReplyKeyboardMarkup, KeyboardButton
        sticky_menu = ReplyKeyboardMarkup(
            [[KeyboardButton("📊 Cập nhật Thể trạng"), KeyboardButton("📜 Danh sách Quest")]],
            resize_keyboard=True
        )
        
        if not response or not response.strip():
            response = "《Báo cáo》 Hệ thống AI không trả về phản hồi nào (Empty Response)."
        
        if keyboard:
            await update.message.reply_text(response, reply_markup=keyboard)
        else:
            await update.message.reply_text(response, reply_markup=sticky_menu)
    except Exception as e:
        logger.error(f"Fatal error in _process_after_delay: {e}", exc_info=True)
        await update.message.reply_text(f"《Lỗi》 Hệ thống gặp sự cố: {str(e)}")


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    message = update.message
    if tg_user is None or message is None:
        return
    
    text = message.text or message.caption or ""
    image_bytes = None
    if message.photo:
        photo_file = await message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
    
    if not text and not image_bytes:
        return
        
    if text == "📜 Danh sách Quest":
        from bot.handlers.quest import handle_quests
        await handle_quests(update, context)
        return
        
    if text == "📊 Cập nhật Thể trạng":
        from bot.handlers.status import handle_status
        await handle_status(update, context)
        return

    # Add to debounce buffer
    if text:
        _pending_messages[tg_user.id].append(text)
    if image_bytes:
        _pending_images[tg_user.id] = image_bytes

    # Cancel existing timer
    if tg_user.id in _debounce_tasks:
        _debounce_tasks[tg_user.id].cancel()
        
    # Start new timer
    _debounce_tasks[tg_user.id] = asyncio.create_task(
        _process_after_delay(tg_user, update, context)
    )
