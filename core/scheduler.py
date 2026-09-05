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
    logger.info(
        "Scheduler configured: reminders every %dm, daily check-in at %02d:%02d",
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
                    "Hôm nay thế nào? Dùng /report để cập nhật."
                ),
                parse_mode="Markdown",
            )
        except Exception as exc:
            logger.error("Failed to send check-in to user %d: %s", user.telegram_id, exc)
