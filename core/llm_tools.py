import logging
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import AsyncSessionLocal
from db.models import Memory, SystemQuest

logger = logging.getLogger(__name__)

async def update_memory_async(user_id: int, content: str) -> str:
    """Updates the user's database with new context or memory."""
    async with AsyncSessionLocal() as session:
        from db.models import Memory
        mem = Memory(user_id=user_id, content=content, importance=10)
        session.add(mem)
        await session.commit()
    return "Đã cập nhật bộ nhớ thành công."

async def cancel_quest_async(quest_id: int, reason: str) -> str:
    """Cancels an active System Quest if the user rejects it or has already done it."""
    async with AsyncSessionLocal() as session:
        quest = await session.get(SystemQuest, quest_id)
        if not quest:
            return "Nhiệm vụ không tồn tại."
        quest.status = "cancelled"
        quest.description += f"\n[Cancelled Reason: {reason}]"
        await session.commit()
    return "Đã hủy nhiệm vụ thành công."

async def complete_quest_async(quest_id: int) -> str:
    """Marks an active System Quest as completed."""
    from datetime import datetime
    async with AsyncSessionLocal() as session:
        quest = await session.get(SystemQuest, quest_id)
        if not quest:
            return "Nhiệm vụ không tồn tại."
        quest.status = "completed"
        quest.completed_at = datetime.utcnow()
        await session.commit()
    return "Đã hoàn thành nhiệm vụ thành công."
