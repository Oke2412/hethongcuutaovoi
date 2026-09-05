"""
bot/handlers/report.py � /report command.
Guided conversation to log physical status, capabilities, and work progress.
Uses ConversationHandler with inline states.
"""
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from db.database import AsyncSessionLocal
from db.models import CapabilityLog, PhysicalStatus, WorkLog, WorkProject
from core.memory import get_or_create_user
from sqlmodel import select

logger = logging.getLogger(__name__)

# Conversation states
(
    CHOOSE_REPORT_TYPE,
    PHYSICAL_ENERGY,
    PHYSICAL_MOOD,
    PHYSICAL_HEALTH,
    PHYSICAL_SLEEP,
    PHYSICAL_NOTES,
    WORK_PROJECT_NAME,
    WORK_PROGRESS,
    WORK_NOTES,
    CAPABILITY_DOMAIN,
    CAPABILITY_LEVEL,
    CAPABILITY_MAX,
    CAPABILITY_UNIT,
) = range(13)


def _score_keyboard(label: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(1, 6)],
        [InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(6, 11)],
    ]
    return InlineKeyboardMarkup(buttons)


async def start_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("? Th? tr?ng", callback_data="physical")],
        [InlineKeyboardButton("?? Ti?n d? c�ng vi?c", callback_data="work")],
        [InlineKeyboardButton("?? Nang l?c", callback_data="capability")],
        [InlineKeyboardButton("? Hu?", callback_data="cancel")],
    ])
    await update.message.reply_text(
        "?? *B�o c�o g�?*", parse_mode="Markdown", reply_markup=keyboard
    )
    return CHOOSE_REPORT_TYPE


# -- Physical status flow --------------------------------------------------

async def choose_report_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == "cancel":
        await query.edit_message_text("�� hu?.")
        return ConversationHandler.END

    context.user_data["report_type"] = choice

    if choice == "physical":
        await query.edit_message_text(
            "? *Nang lu?ng h�m nay?* (1-10)",
            parse_mode="Markdown",
            reply_markup=_score_keyboard("Nang lu?ng"),
        )
        return PHYSICAL_ENERGY

    elif choice == "work":
        await query.edit_message_text(
            "?? *T�n project?* (nh?p text)",
            parse_mode="Markdown",
        )
        return WORK_PROJECT_NAME

    elif choice == "capability":
        await query.edit_message_text(
            "?? *Linh v?c n�o?*\n(VD: coding, fitness, reading, focus...)\nNh?p text:",
            parse_mode="Markdown",
        )
        return CAPABILITY_DOMAIN

    return ConversationHandler.END


async def physical_energy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["energy"] = int(query.data)
    await query.edit_message_text(
        f"? Nang lu?ng: {query.data}/10\n\n?? *T�m tr?ng?* (1-10)",
        parse_mode="Markdown",
        reply_markup=_score_keyboard("T�m tr?ng"),
    )
    return PHYSICAL_MOOD


async def physical_mood(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["mood"] = int(query.data)
    await query.edit_message_text(
        f"? T�m tr?ng: {query.data}/10\n\n?? *S?c kh?e th? ch?t?* (1-10)",
        parse_mode="Markdown",
        reply_markup=_score_keyboard("S?c kh?e"),
    )
    return PHYSICAL_HEALTH


async def physical_health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["health"] = int(query.data)
    await query.edit_message_text(
        f"? S?c kh?e: {query.data}/10\n\n?? *Ng? bao nhi�u ti?ng?* (nh?p s?, VD: 7.5)",
        parse_mode="Markdown",
    )
    return PHYSICAL_SLEEP


async def physical_sleep(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        sleep = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("Nh?p s? th�i nh�. VD: 7 ho?c 7.5")
        return PHYSICAL_SLEEP
    context.user_data["sleep"] = sleep
    await update.message.reply_text(
        "?? *Ghi ch� th�m?* (ho?c g� 'skip')", parse_mode="Markdown"
    )
    return PHYSICAL_NOTES


async def physical_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    notes = update.message.text.strip()
    if notes.lower() == "skip":
        notes = ""

    tg_user = update.effective_user
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_user.id, tg_user.full_name, tg_user.username)
        status = PhysicalStatus(
            user_id=user.id,
            energy=context.user_data["energy"],
            mood=context.user_data["mood"],
            health=context.user_data["health"],
            sleep_hours=context.user_data["sleep"],
            notes=notes,
        )
        session.add(status)
        await session.commit()

    avg = (context.user_data["energy"] + context.user_data["mood"] + context.user_data["health"]) / 3
    await update.message.reply_text(
        f"? *Th? tr?ng d� ghi nh?n.*\n"
        f"Ch? s? trung b�nh: *{avg:.1f}/10*",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


# -- Work progress flow ----------------------------------------------------

async def work_project_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["project_name"] = update.message.text.strip()
    await update.message.reply_text(
        "?? *Ti?n d? hi?n t?i?* (0-100%)\nNh?p s? nguy�n:",
        parse_mode="Markdown",
    )
    return WORK_PROGRESS


async def work_progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        pct = int(update.message.text.strip().replace("%", ""))
        pct = max(0, min(100, pct))
    except ValueError:
        await update.message.reply_text("Nh?p s? nguy�n 0-100 nh�.")
        return WORK_PROGRESS
    context.user_data["progress"] = pct
    await update.message.reply_text(
        "?? *Ghi ch� / ho�n th�nh g� h�m nay?* (ho?c 'skip')",
        parse_mode="Markdown",
    )
    return WORK_NOTES


async def work_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    notes = update.message.text.strip()
    if notes.lower() == "skip":
        notes = ""

    tg_user = update.effective_user
    project_name = context.user_data["project_name"]
    progress = context.user_data["progress"]

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_user.id, tg_user.full_name, tg_user.username)

        # Find or create project
        res = await session.execute(
            select(WorkProject).where(
                WorkProject.user_id == user.id,
                WorkProject.name == project_name,
            )
        )
        project = res.scalar_one_or_none()
        if project is None:
            project = WorkProject(user_id=user.id, name=project_name, progress_percent=progress)
            session.add(project)
            await session.flush()
        else:
            delta = progress - project.progress_percent
            project.progress_percent = progress
            from datetime import datetime
            project.updated_at = datetime.utcnow()
            log = WorkLog(
                project_id=project.id,
                user_id=user.id,
                progress_delta=delta,
                notes=notes,
            )
            session.add(log)

        await session.commit()

    await update.message.reply_text(
        f"? *{project_name}* � {progress}%\n{notes if notes else ''}",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


# -- Capability flow -------------------------------------------------------

async def capability_domain(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["cap_domain"] = update.message.text.strip()
    await update.message.reply_text(
        "?? *M?c hi?n t?i?* (s? � VD: 45 push-ups, 7/10, 3 gi? focus...)\nNh?p s?:",
        parse_mode="Markdown",
    )
    return CAPABILITY_LEVEL


async def capability_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        level = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("Nh?p s? th�i nh�.")
        return CAPABILITY_LEVEL
    context.user_data["cap_level"] = level
    await update.message.reply_text(
        "?? *M?c cao nh?t t? tru?c d?n nay?* (nh?p s?, ho?c 'same' n?u b?ng hi?n t?i)",
        parse_mode="Markdown",
    )
    return CAPABILITY_MAX


async def capability_max(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text.lower() == "same":
        max_val = context.user_data["cap_level"]
    else:
        try:
            max_val = float(text)
        except ValueError:
            await update.message.reply_text("Nh?p s? ho?c 'same'.")
            return CAPABILITY_MAX
    context.user_data["cap_max"] = max(max_val, context.user_data["cap_level"])
    await update.message.reply_text(
        "?? *�on v??* (VD: push-ups, km, gi?, di?m... ho?c 'skip')",
        parse_mode="Markdown",
    )
    return CAPABILITY_UNIT


async def capability_unit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    unit = update.message.text.strip()
    if unit.lower() == "skip":
        unit = ""

    tg_user = update.effective_user
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_user.id, tg_user.full_name, tg_user.username)
        cap = CapabilityLog(
            user_id=user.id,
            domain=context.user_data["cap_domain"],
            current_level=context.user_data["cap_level"],
            max_ever=context.user_data["cap_max"],
            unit=unit,
        )
        session.add(cap)
        await session.commit()

    domain = context.user_data["cap_domain"]
    level = context.user_data["cap_level"]
    max_v = context.user_data["cap_max"]
    pct = int((level / max(max_v, 1)) * 100)
    await update.message.reply_text(
        f"? *{domain}* ghi nh?n: {level} {unit} ({pct}% c?a max {max_v})",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("�� hu?.")
    return ConversationHandler.END


# -- Build ConversationHandler ---------------------------------------------

def build_report_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("report", start_report)],
        states={
            CHOOSE_REPORT_TYPE: [CallbackQueryHandler(choose_report_type)],
            PHYSICAL_ENERGY: [CallbackQueryHandler(physical_energy)],
            PHYSICAL_MOOD: [CallbackQueryHandler(physical_mood)],
            PHYSICAL_HEALTH: [CallbackQueryHandler(physical_health)],
            PHYSICAL_SLEEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, physical_sleep)],
            PHYSICAL_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, physical_notes)],
            WORK_PROJECT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, work_project_name)],
            WORK_PROGRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, work_progress)],
            WORK_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, work_notes)],
            CAPABILITY_DOMAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, capability_domain)],
            CAPABILITY_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, capability_level)],
            CAPABILITY_MAX: [MessageHandler(filters.TEXT & ~filters.COMMAND, capability_max)],
            CAPABILITY_UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, capability_unit)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )
