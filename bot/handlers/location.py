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
    is_live = message.location.live_period is not None

    status_msg = await message.reply_text("⏳ [Đang tính toán ma trận tọa độ...]")

    try:
        tg_user = update.effective_user
        async with AsyncSessionLocal() as session:
            user = await get_or_create_user(session, tg_user.id, tg_user.full_name, tg_user.username)
            
        location_type = "Live Location" if is_live else "Tọa độ tĩnh"
        
        prompt = (
            f"[HỆ THỐNG] Người dùng vừa gửi vị trí GPS ({location_type}): Vĩ độ {lat}, Kinh độ {lon}.\\n"
            f"Dựa vào các [Điểm neo] trong trí nhớ (Mem0), hãy dùng tool `calculate_distance` để xác định ngài ấy đang ở gần địa điểm quen thuộc nào.\\n"
            f"Sau đó, kết hợp với trạng thái thể chất/năng lượng (PhysicalStatus) hiện tại, hãy suy luận xem ngài ấy cần Phần thưởng (Reward) hay Nhiệm vụ phụ (Side Quest)."
        )
        
        response = await brain.process_input(user_id=str(user.id), text_content=prompt)
        await status_msg.edit_text(response)

    except Exception as exc:
        logger.error(f"Error handling location: {exc}", exc_info=True)
        await status_msg.edit_text("⚠️ [Báo cáo lỗi] Đứt gãy tín hiệu định vị.")

def build_location_handler() -> MessageHandler:
    return MessageHandler(filters.LOCATION, handle_location)
