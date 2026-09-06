import logging
from datetime import datetime
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import AsyncSessionLocal
from db.models import Memory, SystemQuest, PhysicalStatus, WorkProject, CapabilityLog

logger = logging.getLogger(__name__)

async def update_memory_async(user_id: int, content: str) -> str:
    """Updates the user's database with new context or memory."""
    async with AsyncSessionLocal() as session:
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
    async with AsyncSessionLocal() as session:
        quest = await session.get(SystemQuest, quest_id)
        if not quest:
            return "Nhiệm vụ không tồn tại."
        quest.status = "completed"
        quest.completed_at = datetime.utcnow()
        await session.commit()
    return "Đã hoàn thành nhiệm vụ thành công."

async def update_physical_status_async(user_id: int, energy: int, mood: int, health: int, sleep_hours: float, notes: str) -> str:
    """Cập nhật trạng thái thể chất của user (PhysicalStatus) vào cuối ngày hoặc khi user than phiền."""
    async with AsyncSessionLocal() as session:
        status = PhysicalStatus(
            user_id=user_id,
            energy=energy,
            mood=mood,
            health=health,
            sleep_hours=sleep_hours,
            notes=notes
        )
        session.add(status)
        await session.commit()
    return "Đã cập nhật thể trạng thành công."

async def manage_project_async(user_id: int, action: str, name: str, progress_percent: int = 0) -> str:
    """Quản lý dự án của user. action có thể là 'add', 'update', hoặc 'delete'."""
    async with AsyncSessionLocal() as session:
        stmt = select(WorkProject).where(WorkProject.user_id == user_id, WorkProject.name == name)
        result = await session.execute(stmt)
        project = result.scalars().first()
        
        if action == "delete":
            if project:
                await session.delete(project)
                await session.commit()
                return f"Đã xóa dự án {name}."
            return f"Không tìm thấy dự án {name} để xóa."
            
        elif action in ["add", "update"]:
            if project:
                project.progress_percent = progress_percent
                project.updated_at = datetime.utcnow()
            else:
                project = WorkProject(user_id=user_id, name=name, progress_percent=progress_percent)
                session.add(project)
            await session.commit()
            return f"Đã cập nhật tiến độ {name} lên {progress_percent}%."
            
        return "Action không hợp lệ."

async def manage_capability_async(user_id: int, action: str, domain: str, level: float, max_ever: float, unit: str = "") -> str:
    """Quản lý kỹ năng của user. action có thể là 'add', 'update', 'delete'."""
    async with AsyncSessionLocal() as session:
        stmt = select(CapabilityLog).where(CapabilityLog.user_id == user_id, CapabilityLog.domain == domain)
        result = await session.execute(stmt)
        cap = result.scalars().first()
        
        if action == "delete":
            if cap:
                await session.delete(cap)
                await session.commit()
                return f"Đã xóa kỹ năng {domain}."
            return "Không tìm thấy kỹ năng."
            
        if action in ["add", "update"]:
            if cap:
                cap.current_level = level
                cap.max_ever = max_ever
            else:
                cap = CapabilityLog(user_id=user_id, domain=domain, current_level=level, max_ever=max_ever, unit=unit)
                session.add(cap)
            await session.commit()
            return f"Đã cập nhật kỹ năng {domain} thành công."
            
        return "Action không hợp lệ."

async def reset_database_async(user_id: int) -> str:
    """Xóa trắng toàn bộ dữ liệu của user trong hệ thống."""
    async with AsyncSessionLocal() as session:
        # Xóa theo thứ tự
        for model in [Memory, SystemQuest, PhysicalStatus, WorkProject, CapabilityLog]:
            stmt = select(model).where(model.user_id == user_id)
            result = await session.execute(stmt)
            for row in result.scalars().all():
                await session.delete(row)
        await session.commit()
    return "Đã xóa trắng (Reset) toàn bộ dữ liệu của ngài thành công."
