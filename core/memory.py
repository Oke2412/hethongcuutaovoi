"""core/memory.py -- Long-term memory operations."""
import logging
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from db.models import CapabilityLog, Memory, PhysicalStatus, Reminder, User, WorkProject

logger = logging.getLogger(__name__)


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    name: str,
    username: str | None = None,
) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=telegram_id, name=name, username=username)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info("New user created: %s (tg_id=%d)", name, telegram_id)
    return user


async def build_user_context(session: AsyncSession, user: User) -> str:
    lines: list[str] = [f"# Context: {user.name}"]

    res = await session.execute(
        select(PhysicalStatus)
        .where(PhysicalStatus.user_id == user.id)
        .order_by(PhysicalStatus.recorded_at.desc())
        .limit(1)
    )
    status = res.scalar_one_or_none()
    if status:
        lines.append(
            f"\n## Thể trạng gần nhất ({status.recorded_at.strftime('%Y-%m-%d')})"
        )
        lines.append(
            f"- Năng lượng: {status.energy}/10"
            f" | Tâm trạng: {status.mood}/10"
            f" | Sức khỏe: {status.health}/10"
            f" | Ngủ: {status.sleep_hours}h"
        )
        if status.notes:
            lines.append(f"- Ghi chú: {status.notes}")
    else:
        lines.append("\n## Thể trạng: chưa có dữ liệu")

    res = await session.execute(
        select(CapabilityLog)
        .where(CapabilityLog.user_id == user.id)
        .order_by(CapabilityLog.recorded_at.desc())
        .limit(20)
    )
    cap_rows = res.scalars().all()
    if cap_rows:
        seen: set[str] = set()
        lines.append("\n## Năng lực hiện tại")
        for c in cap_rows:
            if c.domain not in seen:
                seen.add(c.domain)
                lines.append(f"- {c.domain}: {c.current_level} (max: {c.max_ever}) {c.unit}")

    res = await session.execute(
        select(WorkProject)
        .where(WorkProject.user_id == user.id, WorkProject.status == "active")
        .order_by(WorkProject.updated_at.desc())
        .limit(10)
    )
    projects = res.scalars().all()
    if projects:
        lines.append("\n## Tiến trình công việc")
        for p in projects:
            lines.append(f"- [{p.progress_percent}%] {p.name}")

    res = await session.execute(
        select(Memory)
        .where(Memory.user_id == user.id)
        .order_by(Memory.importance.desc(), Memory.created_at.desc())
        .limit(15)
    )
    memories = res.scalars().all()
    if memories:
        lines.append("\n## Ký ức quan trọng")
        for m in memories:
            lines.append(f"- {m.content}")

    return "\n".join(lines)


async def save_memory(
    session: AsyncSession,
    user: User,
    content: str,
    tags: list[str],
    importance: int = 5,
) -> Memory:
    mem = Memory(user_id=user.id, content=content, tags=",".join(tags), importance=importance)
    session.add(mem)
    await session.commit()
    return mem


MIN_EF = 1.3


def sm2_next(reminder: "Reminder", quality: int) -> "Reminder":
    """Update a Reminder using the SM-2 algorithm. quality: 0-5."""
    if quality < 3:
        reminder.repetitions = 0
        reminder.interval_days = 1.0
    else:
        if reminder.repetitions == 0:
            reminder.interval_days = 1.0
        elif reminder.repetitions == 1:
            reminder.interval_days = 6.0
        else:
            reminder.interval_days = round(reminder.interval_days * reminder.easiness, 1)
        reminder.repetitions += 1
    reminder.easiness = max(
        MIN_EF,
        reminder.easiness + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02),
    )
    reminder.next_remind_at = datetime.utcnow() + timedelta(days=reminder.interval_days)
    return reminder


async def get_due_reminders(session: AsyncSession, user: User) -> list[Reminder]:
    result = await session.execute(
        select(Reminder).where(
            Reminder.user_id == user.id,
            Reminder.is_active == True,
            Reminder.next_remind_at <= datetime.utcnow(),
        )
    )
    return list(result.scalars().all())
