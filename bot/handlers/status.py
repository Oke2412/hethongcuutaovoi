"""bot/handlers/status.py -- /status command."""
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes
from sqlmodel import select

from db.database import AsyncSessionLocal
from db.models import CapabilityLog, PhysicalStatus, WorkProject
from core.memory import get_or_create_user

logger = logging.getLogger(__name__)


def _bar(value: int, total: int = 10) -> str:
    filled = max(0, min(total, value))
    return '\u2588' * filled + '\u2591' * (total - filled)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    if tg_user is None:
        return

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_user.id, tg_user.full_name, tg_user.username)

        res = await session.execute(
            select(PhysicalStatus)
            .where(PhysicalStatus.user_id == user.id)
            .order_by(PhysicalStatus.recorded_at.desc())
            .limit(1)
        )
        status = res.scalar_one_or_none()

        res = await session.execute(
            select(CapabilityLog)
            .where(CapabilityLog.user_id == user.id)
            .order_by(CapabilityLog.recorded_at.desc())
            .limit(30)
        )
        cap_rows = res.scalars().all()
        seen: set[str] = set()
        caps: list[CapabilityLog] = []
        for c in cap_rows:
            if c.domain not in seen:
                seen.add(c.domain)
                caps.append(c)

        res = await session.execute(
            select(WorkProject)
            .where(WorkProject.user_id == user.id, WorkProject.status == 'active')
            .order_by(WorkProject.updated_at.desc())
        )
        projects = res.scalars().all()

    sep = '\u2550' * 22
    lines = [
        '\u256c' + sep + '\u256c',
        '\u2551' + '  \U0001f4ca  SYSTEM STATUS   ' + '\u2551',
        '\u255a' + sep + '\u255d',
        '',
        f'\U0001f464 *{user.name}*',
        f'\U0001f550 {datetime.now().strftime("%Y-%m-%d %H:%M")}',
        '',
        '\u26a1 *Th\u1ec3 tr\u1ea1ng*',
    ]

    if status:
        lines += [
            f'  N\u0103ng l\u01b0\u1ee3ng: [{_bar(status.energy)}] {status.energy}/10',
            f'  T\u00a2m tr\u1ea1ng:  [{_bar(status.mood)}] {status.mood}/10',
            f'  S\u1ee9c kh\u1ecfe:   [{_bar(status.health)}] {status.health}/10',
            f'  Ng\u1ee7: {status.sleep_hours}h  |  {status.recorded_at.strftime("%d/%m")}',
        ]
        if status.notes:
            lines.append(f'  \U0001f4dd {status.notes}')
    else:
        lines.append('  _(ch\u01b0a c\u00f4 d\u1eef li\u1ec7\u2014 d\u00fang /report)_')

    lines += ['', '\U0001f9e0 *N\u0103ng l\u1eef1c*']
    if caps:
        for c in caps:
            pct = int((c.current_level / max(c.max_ever, 1)) * 10)
            lines.append(f'  {c.domain}: [{_bar(pct)}] {c.current_level}/{c.max_ever} {c.unit}')
    else:
        lines.append('  _(ch\u01b0a c\u00f4 \u2014 d\u00fang /report)_')

    lines += ['', '\U0001f4bc *Ti\u1ebfn tr\u00ecnh c\u00f4ng vi\u1ec7c*']
    if projects:
        for p in projects:
            filled = p.progress_percent // 10
            lines.append(f'  [{_bar(filled)}] {p.progress_percent}% \u2014 {p.name}')
    else:
        lines.append('  _(ch\u01b0a c\u00f4 project \u2014 d\u00fang /report)_')

    await update.message.reply_text('\n'.join(lines), parse_mode='Markdown')
