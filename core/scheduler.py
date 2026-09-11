"""core/scheduler.py -- APScheduler setup."""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from config import settings

logger = logging.getLogger(__name__)
_scheduler: AsyncIOScheduler | None = None


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    global _scheduler
    _scheduler = AsyncIOScheduler(timezone="Asia/Ho_Chi_Minh")

    _scheduler.add_job(
        _send_due_reminders,
        trigger="interval",
        minutes=settings.reminder_check_interval_minutes,
        args=[bot],
        id="reminder_check",
        replace_existing=True,
    )
    _scheduler.add_job(
        _send_daily_checkin,
        trigger="cron",
        hour=settings.daily_checkin_hour,
        minute=settings.daily_checkin_minute,
        args=[bot],
        id="daily_checkin",
        replace_existing=True,
    )
    _scheduler.add_job(
        _generate_morning_quests,
        trigger="cron",
        hour=6,
        minute=30,
        args=[bot],
        id="morning_quests",
        replace_existing=True,
    )

    _scheduler.add_job(
        _check_expired_quests,
        trigger="interval",
        minutes=5,
        args=[bot],
        id="check_expired_quests",
        replace_existing=True,
    )
    logger.info(

        "Scheduler configured: reminders every %dm, daily check-in at %02d:%02d, quests at 06:30",
        settings.reminder_check_interval_minutes,
        settings.daily_checkin_hour,
        settings.daily_checkin_minute,
    )
    return _scheduler


async def _send_due_reminders(bot: Bot) -> None:
    from db.database import AsyncSessionLocal
    from db.models import User
    from core.memory import get_due_reminders, sm2_next
    from sqlmodel import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        for user in users:
            due = await get_due_reminders(session, user)
            for reminder in due:
                try:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=f"🔔 *Nhắc nhở*\n{reminder.content}",
                        parse_mode="Markdown",
                    )
                    sm2_next(reminder, quality=3)
                    session.add(reminder)
                except Exception as exc:
                    logger.error("Failed to send reminder %d: %s", reminder.id, exc)
        await session.commit()


async def _send_daily_checkin(bot: Bot) -> None:
    from db.database import AsyncSessionLocal
    from db.models import User
    from sqlmodel import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

    for user in users:
        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text=(
                    "📋 *Điểm danh cuối ngày*\n\n"
                    "Hôm nay thế nào? Hãy báo cáo lại tình trạng của bạn."
                ),
                parse_mode="Markdown",
            )
        except Exception as exc:
            logger.error("Failed to send check-in to user %d: %s", user.telegram_id, exc)

async def _generate_morning_quests(bot: Bot) -> None:
    from db.database import AsyncSessionLocal
    from db.models import User
    from sqlmodel import select
    from core.quest_generator import generate_and_save_quest

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

    for user in users:
        try:
            quests = await generate_and_save_quest(user.id)
            if not quests:
                continue
            
            text = "🌅 *[Thông báo] Hệ thống hoàn tất phân tích buổi sáng.*\n\nPhát sinh Nhiệm vụ Hệ thống:\n"
            for i, q in enumerate(quests, 1):
                text += f"\n*{i}. {q.get('title')}*\n"
                text += f"- Lý do: {q.get('description')}\n"
                text += f"- Phần thưởng: {q.get('reward')}\n"
            
            await bot.send_message(
                chat_id=user.telegram_id,
                text=text,
                parse_mode="Markdown",
            )
        except Exception as exc:
            logger.error("Failed to generate quest for user %d: %s", user.telegram_id, exc)

async def _check_expired_quests(bot: Bot) -> None:
    from db.database import AsyncSessionLocal
    from db.models import User, SystemQuest
    from sqlmodel import select
    from datetime import datetime
    import asyncio
    from core.llm_tools import update_physical_status_async
    
    async with AsyncSessionLocal() as session:
        now = datetime.utcnow()
        result = await session.execute(
            select(SystemQuest).where(SystemQuest.status == "pending", SystemQuest.expires_at != None, SystemQuest.expires_at <= now)
        )
        expired_quests = result.scalars().all()
        
        for q in expired_quests:
            q.status = "failed"
            session.add(q)
            
            # Fetch user to notify
            user_res = await session.execute(select(User).where(User.id == q.user_id))
            user = user_res.scalars().first()
            if user:
                # Apply penalty silently (e.g. -5HP) by extracting integer if possible, else default -5
                penalty_val = -5
                import re
                hp_match = re.search(r'\d+', q.penalty)
                if hp_match:
                    penalty_val = -int(hp_match.group())
                
                await update_physical_status_async(user.id, energy=5, mood=5, health=penalty_val, sleep_hours=0, notes=f"Failed quest: {q.title}")
                
                try:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=f"⏳ **[HỆ THỐNG] Nhiệm vụ Hết hạn:** {q.title}\n_Trạng thái: FAILED_\n_Hình phạt: {q.penalty}_",
                        parse_mode="Markdown",
                    )
                except Exception as exc:
                    logger.error("Failed to notify user %d of expired quest: %s", user.telegram_id, exc)
                    
        if expired_quests:
            await session.commit()
