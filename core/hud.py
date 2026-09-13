from db.database import AsyncSessionLocal
from sqlmodel import select
from db.models import User, PhysicalStatus, SystemQuest
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

async def build_hud(user_id: int) -> tuple[str, InlineKeyboardMarkup | None]:
    """Returns (hud_line, keyboard) from current DB state."""
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            return "━━━━━━━━━━━━━━━━━━━━━\n⚡ ? | 😐 ? | ❤️ ? | 💎 ?cr | 📍 H3:?", None
            
        stmt_phys = select(PhysicalStatus).where(PhysicalStatus.user_id == user_id).order_by(PhysicalStatus.id.desc()).limit(1)
        phys = (await session.execute(stmt_phys)).scalars().first()
        
        energy = phys.energy if phys else "?"
        mood = phys.mood if phys else "?"
        health = phys.health if phys else "?"
        credits = user.credits if user else 0
        
        # Get hex_id from location state
        try:
            from bot.handlers.location import _location_state
            loc_data = _location_state.get(user.telegram_id if user else user_id)
            hex_id = loc_data["hex"] if loc_data else "?"
        except ImportError:
            hex_id = "?"
            
        hud_line = f"━━━━━━━━━━━━━━━━━━━━━\n⚡ {energy}/10 | 😐 {mood}/10 | ❤️ {health}/10 | 💎 {credits}cr | 📍 H3:{hex_id}"
        
        stmt_quest = select(SystemQuest).where(SystemQuest.user_id == user_id, SystemQuest.status == "pending")
        quests = (await session.execute(stmt_quest)).scalars().all()
        
        keyboard = None
        if quests:
            buttons = []
            for q in quests:
                short_title = (q.title[:20] + '..') if q.title and len(q.title) > 20 else (q.title or f"Quest #{q.id}")
                buttons.append([
                    InlineKeyboardButton(f"✅ Hoàn thành: {short_title}", callback_data=f"complete_{q.id}"),
                    InlineKeyboardButton("❌ Hủy", callback_data=f"cancel_{q.id}")
                ])
            keyboard = InlineKeyboardMarkup(buttons)
            
        return hud_line, keyboard
