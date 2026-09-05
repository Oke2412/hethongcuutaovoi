"""bot/handlers/start.py -- /start command handler."""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from db.database import AsyncSessionLocal
from core.memory import get_or_create_user

logger = logging.getLogger(__name__)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user is None:
        return
    async with AsyncSessionLocal() as session:
        await get_or_create_user(
            session,
            telegram_id=user.id,
            name=user.full_name,
            username=user.username,
        )
    await update.message.reply_text(
        "⚔️ *Hệ Thống Khởi Động*\n\n"
        f"Chào mừng, *{user.full_name}*.\n\n"
        "Các lệnh có sẵn:\n"
        "• /onboard — Thiết lập thông tin cá nhân (context) ban đầu\n"
        "• /status — Xem tổng quan hiện tại\n"
        "• /quests — Danh sách Nhiệm vụ hệ thống\n"
        "• /report — Cập nhật thể trạng & tiến độ\n"
        "• /remind — Quản lý nhắc nhở\n"
        "• Hoặc chỉ cần nhắn tin bình thường.",
        parse_mode="Markdown",
    )
