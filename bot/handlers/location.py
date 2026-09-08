import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from core.brain import brain
from db.database import AsyncSessionLocal
from core.memory import get_or_create_user

logger = logging.getLogger(__name__)

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message or not message.location:
        return

    lat = message.location.latitude
    lon = message.location.longitude

    try:
        tg_user = update.effective_user
        async with AsyncSessionLocal() as session:
            user = await get_or_create_user(session, tg_user.id, tg_user.full_name, tg_user.username)
            
        # 1. Gọi Spatial Engine (Tính toán offline, 0 API cost)
        from core.spatial import process_location
        spatial_event = await process_location(user.id, lat, lon)

        if not spatial_event:
            # Hoàn toàn im lặng nếu chỉ là di chuyển bình thường
            return

        # 2. Nếu có Event -> Gửi thông báo đang suy nghĩ
        status_msg = await message.reply_text("🧭 [Hệ thống đang rà soát dữ liệu Không gian...]")
        
        from core.llm import evaluate_and_generate_side_quest_async
        event_trigger = f"User vừa có sự kiện di chuyển: {spatial_event} tại tọa độ ({lat}, {lon}). Hãy kiểm tra xem đây là nơi nào và giao Side Quest."
        
        side_quest_text = await evaluate_and_generate_side_quest_async(user.id, event_trigger)
        
        if side_quest_text:
            await status_msg.edit_text(f"📍 Sự kiện: {spatial_event}\n\n{side_quest_text}")
        else:
            # LLM quyết định im lặng -> Xóa luôn tin nhắn "đang suy nghĩ"
            await status_msg.delete()

    except Exception as exc:
        logger.error(f"Error handling location: {exc}", exc_info=True)
        # Chỉ gửi lỗi nếu thực sự là một lỗi crash nghiêm trọng (tùy chọn)

def build_location_handler() -> MessageHandler:
    return MessageHandler(filters.LOCATION, handle_location)
