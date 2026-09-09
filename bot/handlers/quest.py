"""bot/handlers/quest.py -- Command to view active system quests."""
import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from sqlmodel import select

from db.database import AsyncSessionLocal
from db.models import SystemQuest
from core.memory import get_or_create_user

logger = logging.getLogger(__name__)

async def handle_quests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    if not tg_user:
        return
        
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_user.id, tg_user.full_name, tg_user.username)
        
        result = await session.execute(
            select(SystemQuest).where(SystemQuest.user_id == user.id, SystemQuest.status == "pending")
        )
        quests = result.scalars().all()
        
        if not quests:
            await update.message.reply_text("✨ Hiện tại không có Nhiệm vụ Hệ thống nào đang chờ xử lý.")
            return
            
        text = "📜 *Danh sách Nhiệm vụ Hệ thống Đang chờ:*\n\n"
        for q in quests:
            text += f"🔹 *[ID: {q.id}] {q.title}*\n"
            text += f"   - Mô tả: {q.description}\n"
            text += f"   - Phần thưởng: 🎁 {q.reward}\n\n"
            
        text += "💡 *Mẹo:* Bạn có thể xác nhận hoàn thành, từ chối hoặc báo cáo lại (ví dụ 'Tôi đã làm xong nhiệm vụ ID 2', 'Hủy nhiệm vụ 1 vì nay ốm') bằng cách chat trực tiếp."
        
        await update.message.reply_text(text, parse_mode="Markdown")

from telegram.ext import CallbackQueryHandler
from core.llm_tools import complete_quest_async, cancel_quest_async

async def handle_quest_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, user_id, update.effective_user.full_name, update.effective_user.username)
        internal_id = user.id
    
    data = query.data
    if data.startswith("complete_"):
        q_id = int(data.split("_")[1])
        res = await complete_quest_async(internal_id, q_id)
        # Edit HUD message to remove buttons
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
        await query.message.reply_text(res)
    elif data.startswith("cancel_"):
        q_id = int(data.split("_")[1])
        res = await cancel_quest_async(internal_id, q_id)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
        await query.message.reply_text(res)

def build_quest_handlers() -> list:
    return [
        CommandHandler("quests", handle_quests),
        CallbackQueryHandler(handle_quest_callback, pattern="^(complete_|cancel_)")
    ]
