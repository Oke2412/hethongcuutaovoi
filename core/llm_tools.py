import asyncio
import logging
from datetime import datetime
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import AsyncSessionLocal
from db.models import Memory, SystemQuest, PhysicalStatus, WorkProject, CapabilityLog, User, MessageLog

logger = logging.getLogger(__name__)

async def update_memory_async(user_id: int, content: str) -> str:
    """Updates the user's database with new context or memory into GraphRAG."""
    from core.brain import brain
    from datetime import datetime
    import asyncio
    
    current_time = datetime.now().isoformat()
    # Write to Mem0 (Chroma + Neo4j) instead of old SQLite table
    await asyncio.to_thread(
        brain.memory.add,
        messages=[{"role": "user", "content": "Master requested memory update"}, {"role": "assistant", "content": content}],
        user_id=str(user_id),
        metadata={"timestamp": current_time, "source": "llm_tool_forced"}
    )
    return "Đã cập nhật Ký ức (Graph) thành công."



async def cancel_quest_async(user_id: int, quest_id: int, reason: str = "Hủy bởi User") -> str:
    """Cancels an active System Quest if the user rejects it or has already done it."""
    async with AsyncSessionLocal() as session:
        quest = await session.get(SystemQuest, quest_id)
        if not quest or quest.user_id != user_id:
            return "Nhiệm vụ không tồn tại hoặc không thuộc về bạn."
        quest.status = "cancelled"
        quest.description += f"\n[Cancelled Reason: {reason}]"
        await session.commit()
    return "Đã hủy nhiệm vụ thành công."

async def complete_quest_async(user_id: int, quest_id: int) -> str:
    """Marks an active System Quest as completed and grants the reward."""
    async with AsyncSessionLocal() as session:
        quest = await session.get(SystemQuest, quest_id)
        if not quest or quest.user_id != user_id:
            return "Nhiệm vụ không tồn tại hoặc không thuộc về bạn."
        
        if quest.status == "completed":
            return "Nhiệm vụ này đã được hoàn thành trước đó."
            
        quest.status = "completed"
        quest.completed_at = datetime.utcnow()
        
        # Grant reward
        user = await session.get(User, user_id)
        if user:
            import re
            match = re.search(r'[-+]?\d*\.\d+|\d+', quest.reward)
            if match:
                user.credits += float(match.group(0))
            
        await session.commit()
    return f"Đã hoàn thành nhiệm vụ! Bạn nhận được {quest.reward} Credits."

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

async def manage_capability_async(user_id: int, action: str, domain: str, level: float, exp: float, unit: str = "") -> str:
    """Quản lý kỹ năng (Level/EXP) của user. action có thể là 'add', 'update', 'delete'."""
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
                cap.exp = exp
                if level > cap.max_ever:
                    cap.max_ever = level
            else:
                cap = CapabilityLog(user_id=user_id, domain=domain, current_level=level, exp=exp, max_ever=level, unit=unit)
                session.add(cap)
            await session.commit()
            return f"Đã cập nhật kỹ năng {domain}: Lv.{level} (EXP: {exp})."
            
        return "Action không hợp lệ."

async def manage_credits_async(user_id: int, action: str, amount: float, reason: str) -> str:
    """Quản lý Tín chỉ (Credits) của user (Cộng/Trừ khi thưởng/phạt)."""
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            return "Không tìm thấy User."
            
        if action == "add":
            user.credits += amount
            await session.commit()
            return f"Đã cộng {amount} Tín chỉ. Số dư: {user.credits}. Lý do: {reason}."
        elif action == "spend":
            if user.credits < amount:
                return f"Giao dịch thất bại. Số dư ({user.credits}) không đủ để trừ {amount} Tín chỉ."
            user.credits -= amount
            await session.commit()
            return f"Đã trừ {amount} Tín chỉ. Số dư: {user.credits}. Lý do: {reason}."
            
        return "Action không hợp lệ."


async def manage_user_status_async(user_id: int, action: str, buff_name: str = "", title: str = "", expires_in_minutes: int = 0) -> str:
    """Quản lý Buff (Overdrive/Debuff) hoặc Title của user."""
    from datetime import timedelta
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            return "Không tìm thấy User."
            
        if action == "set_buff":
            user.active_buff = buff_name
            if expires_in_minutes > 0:
                user.buff_expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
            else:
                user.buff_expires_at = None
            await session.commit()
            return f"Đã thiết lập trạng thái: {buff_name} (Hết hạn sau {expires_in_minutes} phút)."
            
        elif action == "clear_buff":
            user.active_buff = ""
            user.buff_expires_at = None
            await session.commit()
            return "Đã xóa trạng thái Buff/Debuff hiện tại."
            
        elif action == "add_title":
            current_titles = [t.strip() for t in user.titles.split(",") if t.strip()]
            if title not in current_titles:
                current_titles.append(title)
                user.titles = ", ".join(current_titles)
                await session.commit()
                return f"Đã mở khóa và trang bị danh hiệu: [{title}]."
            return f"Ngài đã có sẵn danh hiệu [{title}] rồi."
            
        return "Action không hợp lệ."

async def create_quest_async(user_id: int, title: str, description: str, reward: str, penalty: str, parent_quest_id: int = 0) -> str:
    """Tạo một Nhiệm vụ mới (Quest) hoặc chuỗi kỹ năng (Cây Kỹ Năng) nếu có parent_quest_id."""
    async with AsyncSessionLocal() as session:
        quest = SystemQuest(
            user_id=user_id,
            title=title,
            description=description,
            reward=reward,
            penalty=penalty,
            parent_quest_id=parent_quest_id if parent_quest_id > 0 else None,
            status="pending"
        )
        session.add(quest)
        await session.commit()
        
        # Lấy ID vừa tạo
        await session.refresh(quest)
        return f"Đã tạo Quest ID {quest.id}: {title} thành công."


def calculate_distance_sync(lat1: float, lon1: float, lat2: float, lon2: float) -> str:
    """Tính khoảng cách (mét) giữa 2 tọa độ GPS bằng công thức Haversine (không tốn API)."""
    import math
    R = 6371000  # Bán kính Trái Đất tính bằng mét
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)




    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return f"Khoảng cách: {distance:.2f} mét."

async def reset_database_async(user_id: int) -> str:
    """Xoa trang toan bo du lieu cua user: SQLite + Mem0 (ChromaDB) + Neo4j (GraphRAG)."""
    results = []

    # 1. Wipe SQLite tables
    async with AsyncSessionLocal() as session:
        for table_model in [Memory, SystemQuest, PhysicalStatus, WorkProject, CapabilityLog, MessageLog]:
            stmt = select(table_model).where(table_model.user_id == user_id)
            result = await session.execute(stmt)
            for row in result.scalars().all():
                await session.delete(row)

        user = await session.get(User, user_id)
        if user:
            user.credits = 0.0
            user.titles = ""
            user.active_buff = ""
            user.buff_expires_at = None

        await session.commit()
    results.append("SQLite: OK")

    # 2. Wipe Mem0 vector memory (ChromaDB)
    try:
        from core.brain import brain
        # Mem0 v2: delete_all uses filters={} like search()
        await asyncio.to_thread(
            brain.memory.delete_all,
            filters={"user_id": str(user_id)},
        )
        results.append("Mem0/ChromaDB: OK")
    except TypeError:
        # Fallback for older Mem0 versions that still accept user_id directly
        try:
            from core.brain import brain
            await asyncio.to_thread(brain.memory.delete_all, user_id=str(user_id))
            results.append("Mem0/ChromaDB: OK (legacy API)")
        except Exception as exc:
            logger.error("Mem0 delete_all failed: %s", exc)
            results.append(f"Mem0/ChromaDB: FAILED ({exc})")
    except Exception as exc:
        logger.error("Mem0 delete_all failed: %s", exc)
        results.append(f"Mem0/ChromaDB: FAILED ({exc})")

    # 3. Wipe Neo4j graph nodes for this user
    try:
        from neo4j import AsyncGraphDatabase
        from config import settings
        neo4j_uri = getattr(settings, "neo4j_uri", "neo4j://localhost:7687")
        neo4j_user = getattr(settings, "neo4j_user", "neo4j")
        neo4j_password = getattr(settings, "neo4j_password", "password")

        async with AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password)) as driver:
            async with driver.session() as neo_session:
                # Delete the user node and all their LifeEvents
                await neo_session.run(
                    """
                    MATCH (u:User {id: $uid})
                    OPTIONAL MATCH (u)-[:EXPERIENCED]->(e:LifeEvent)
                    DETACH DELETE u, e
                    """,
                    uid=user_id,
                )
        results.append("Neo4j: OK")
    except ImportError:
        results.append("Neo4j: SKIPPED (neo4j driver not installed)")
    except Exception as exc:
        logger.error("Neo4j reset failed: %s", exc)
        results.append(f"Neo4j: FAILED ({exc})")

    summary = " | ".join(results)
    return f"[Reset hoan tat] {summary}"

