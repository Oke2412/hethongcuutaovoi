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
        
        # Get Omni Context
        from sqlalchemy.future import select
        from db.models import SpatialState, PhysicalStatus
        from datetime import datetime
        
        # Time
        current_time = datetime.now().strftime("%H:%M, Ngày %d/%m/%Y")
        
        # Location
        stmt_spatial = select(SpatialState).where(SpatialState.user_id == user.id)
        res_spatial = await session.execute(stmt_spatial)
        spatial = res_spatial.scalars().first()
        loc_str = "Chưa rõ"
        if spatial:
            loc_str = f"Trạng thái: {spatial.current_state} (Lat: {spatial.last_lat}, Lon: {spatial.last_lon})"
            if spatial.current_state == "STATIONARY":
                loc_str += f" - Dừng lại từ lúc {spatial.state_updated_at.strftime('%H:%M')}"
                
        # Status
        stmt_phys = select(PhysicalStatus).where(PhysicalStatus.user_id == user.id).order_by(PhysicalStatus.recorded_at.desc())
        res_phys = await session.execute(stmt_phys)
        phys = res_phys.scalars().first()
        phys_str = "Chưa báo cáo"
        if phys:
            phys_str = f"Energy {phys.energy}/10, Mood {phys.mood}/10, Health {phys.health}/10"

    injected_text = (
        f"[BỐI CẢNH HIỆN TẠI]\n"
        f"- Thời gian thực: {current_time}\n"
        f"- Định vị: {loc_str}\n"
        f"- Thể trạng: {phys_str}\n"
        f"[TIN NHẮN CỦA USER]\n{message.text}"
    )

    # Delegate entirely to the Core Brain
    response = await brain.process_input(user_id=str(user.id), text_content=injected_text)
    await message.reply_text(response)
