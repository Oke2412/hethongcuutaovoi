"""bot/handlers/onboard.py -- /onboard command."""
import logging
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters,
)
from db.database import AsyncSessionLocal
from db.models import CapabilityLog, Memory, PhysicalStatus, WorkProject
from core.memory import get_or_create_user

logger = logging.getLogger(__name__)

(
    OB_CAP_DOMAIN, OB_CAP_LEVEL, OB_CAP_MAX, OB_CAP_UNIT, OB_MORE_CAPS,
    OB_PHYS_ENERGY, OB_PHYS_MOOD, OB_PHYS_HEALTH, OB_PHYS_SLEEP,
    OB_PROJECT_NAME, OB_PROJECT_PROGRESS, OB_MORE_PROJECTS,
    OB_MEMORY, OB_MORE_MEMORY,
) = range(14)


def _score_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(1, 6)],
        [InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(6, 11)],
    ])


def _yn_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Có, thêm nữa", callback_data="yes"),
        InlineKeyboardButton("❌ Xong rồi", callback_data="no"),
    ]])


# ---- Entry ----
async def start_onboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tg_user = update.effective_user
    async with AsyncSessionLocal() as session:
        await get_or_create_user(session, tg_user.id, tg_user.full_name, tg_user.username)
    context.user_data.clear()
    context.user_data["caps"] = []
    context.user_data["projects"] = []
    context.user_data["memories"] = []
    await update.message.reply_text(
        "⚔️ *Onboarding Hệ Thống*\n"
        "\nTôi sẽ hỏi một số câu để thiết lập profile của bạn.\n"
        "Gõ *skip* để bỏ qua bước bất kỳ.\n"
        "\n🧠 *Bước 1/4: Năng lực*\n"
        "\nBạn muốn theo dõi năng lực gì?\n"
        "VD: `coding`, `fitness`, `reading`, `focus`...\n"
        "\nNhập tên lĩnh vực đầu tiên:",
        parse_mode="Markdown",
    )
    return OB_CAP_DOMAIN


# ---- Capability flow ----
async def ob_cap_domain(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text.lower() == "skip":
        return await _ask_physical(update.message)
    context.user_data["cur_domain"] = text
    await update.message.reply_text(
        f"📊 *{text}* — mức hiện tại? (số, VD: 45, 7.5...):",
        parse_mode="Markdown",
    )
    return OB_CAP_LEVEL


async def ob_cap_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        level = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("Nhập số thôi nhé.")
        return OB_CAP_LEVEL
    context.user_data["cur_level"] = level
    await update.message.reply_text("🏆 *Max từ trước đến nay?* (số hoặc `same`):", parse_mode="Markdown")
    return OB_CAP_MAX


async def ob_cap_max(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    cur = context.user_data["cur_level"]
    try:
        max_val = cur if text.lower() == "same" else float(text)
    except ValueError:
        max_val = cur
    context.user_data["cur_max"] = max(cur, max_val)
    await update.message.reply_text("📏 *Đơn vị?* (VD: push-ups, km, giờ...) hoặc `skip`:", parse_mode="Markdown")
    return OB_CAP_UNIT


async def ob_cap_unit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    unit = update.message.text.strip()
    if unit.lower() == "skip":
        unit = ""
    d = context.user_data["cur_domain"]
    lv = context.user_data["cur_level"]
    mx = context.user_data["cur_max"]
    context.user_data["caps"].append({"domain": d, "level": lv, "max": mx, "unit": unit})
    await update.message.reply_text(
        f"✅ *{d}*: {lv}/{mx} {unit}\n\nThêm lĩnh vực nào nữa không?",
        parse_mode="Markdown", reply_markup=_yn_kb(),
    )
    return OB_MORE_CAPS


async def ob_more_caps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    if q.data == "yes":
        await q.edit_message_text("Nhập tên lĩnh vực tiếp theo:")
        return OB_CAP_DOMAIN
    n = len(context.user_data["caps"])
    await q.edit_message_text(f"✅ {n} lĩnh vực đã ghi.")
    return await _ask_physical(q.message)


async def _ask_physical(message) -> int:
    await message.reply_text(
        "⚡ *Bước 2/4: Thể trạng*\n\nNăng lượng hôm nay? (1-10)",
        parse_mode="Markdown", reply_markup=_score_kb(),
    )
    return OB_PHYS_ENERGY


# ---- Physical flow ----
async def ob_phys_energy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query; await q.answer()
    context.user_data["energy"] = int(q.data)
    await q.edit_message_text(
        f"✅ Năng lượng: {q.data}/10\n\n😊 Tâm trạng? (1-10)",
        parse_mode="Markdown", reply_markup=_score_kb(),
    )
    return OB_PHYS_MOOD


async def ob_phys_mood(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query; await q.answer()
    context.user_data["mood"] = int(q.data)
    await q.edit_message_text(
        f"✅ Tâm trạng: {q.data}/10\n\n💪 Sức khỏe thể chất? (1-10)",
        parse_mode="Markdown", reply_markup=_score_kb(),
    )
    return OB_PHYS_HEALTH


async def ob_phys_health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query; await q.answer()
    context.user_data["health"] = int(q.data)
    await q.edit_message_text(
        f"✅ Sức khỏe: {q.data}/10\n\n🌙 Ngủ bao nhiêu tiếng? (VD: 7.5)",
        parse_mode="Markdown",
    )
    return OB_PHYS_SLEEP


async def ob_phys_sleep(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["sleep"] = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("Nhập số thôi nhé, VD: 7 hoặc 7.5")
        return OB_PHYS_SLEEP
    await update.message.reply_text(
        "💼 *Bước 3/4: Dự án / Công việc*\n\nBạn đang làm gì? Nhập tên dự án (hoặc `skip`):",
        parse_mode="Markdown",
    )
    return OB_PROJECT_NAME


# ---- Project flow ----
async def ob_project_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text.lower() == "skip":
        return await _ask_memory(update.message)
    context.user_data["cur_project"] = text
    await update.message.reply_text(
        f"📊 *{text}* — tiến độ hiện tại? (0–100):",
        parse_mode="Markdown",
    )
    return OB_PROJECT_PROGRESS


async def ob_project_progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        pct = max(0, min(100, int(update.message.text.strip().replace("%", ""))))
    except ValueError:
        await update.message.reply_text("Nhập số 0–100.")
        return OB_PROJECT_PROGRESS
    name = context.user_data["cur_project"]
    context.user_data["projects"].append({"name": name, "progress": pct})
    await update.message.reply_text(
        f"✅ *{name}* — {pct}%\n\nThêm dự án nào nữa không?",
        parse_mode="Markdown", reply_markup=_yn_kb(),
    )
    return OB_MORE_PROJECTS


async def ob_more_projects(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query; await q.answer()
    if q.data == "yes":
        await q.edit_message_text("Tên dự án tiếp theo:")
        return OB_PROJECT_NAME
    n = len(context.user_data["projects"])
    await q.edit_message_text(f"✅ {n} dự án đã ghi.")
    return await _ask_memory(q.message)


async def _ask_memory(message) -> int:
    await message.reply_text(
        "🧠 *Bước 4/4: Thông tin cần nhớ*\n"
        "\nCó điều gì quan trọng tôi nên biết về bạn không?\n"
        "(VD: mục tiêu, sở thích, thói quen...)\n"
        "Nhập từng ý một, hoặc `skip`:",
        parse_mode="Markdown",
    )
    return OB_MEMORY


# ---- Memory flow ----
async def ob_memory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text.lower() == "skip":
        await _save_and_finish(update.effective_user, context, update.message)
        return ConversationHandler.END
    context.user_data["memories"].append(text)
    await update.message.reply_text(
        f"✅ _{text}_\n\nChêm chưa? Thêm gì nữa không?",
        parse_mode="Markdown", reply_markup=_yn_kb(),
    )
    return OB_MORE_MEMORY


async def ob_more_memory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query; await q.answer()
    if q.data == "yes":
        await q.edit_message_text("Nhập thêm:")
        return OB_MEMORY
    n = len(context.user_data["memories"])
    await q.edit_message_text(f"✅ {n} ký ức đã ghi.")
    await _save_and_finish(q.from_user, context, q.message)
    return ConversationHandler.END


# ---- Save & summary ----
async def _save_and_finish(tg_user, context: ContextTypes.DEFAULT_TYPE, message) -> None:
    data = context.user_data
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_user.id, tg_user.full_name, tg_user.username)
        for cap in data.get("caps", []):
            session.add(CapabilityLog(
                user_id=user.id, domain=cap["domain"],
                current_level=cap["level"], max_ever=cap["max"], unit=cap["unit"],
            ))
        if data.get("energy") is not None:
            session.add(PhysicalStatus(
                user_id=user.id, energy=data["energy"],
                mood=data["mood"], health=data["health"],
                sleep_hours=data.get("sleep", 0),
            ))
        for proj in data.get("projects", []):
            session.add(WorkProject(
                user_id=user.id, name=proj["name"],
                progress_percent=proj["progress"],
                updated_at=datetime.utcnow(),
            ))
        for mem in data.get("memories", []):
            session.add(Memory(user_id=user.id, content=mem, importance=8))
        await session.commit()
    caps  = len(data.get("caps", []))
    projs = len(data.get("projects", []))
    mems  = len(data.get("memories", []))
    await message.reply_text(
        "⚔️ *Onboarding hoàn tất!*\n"
        f"\n🧠 Năng lực: {caps} lĩnh vực"
        f"\n💼 Dự án: {projs}"
        f"\n📝 Ký ức: {mems} mục"
        "\n\nDùng /status để xem tổng quan!",
        parse_mode="Markdown",
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Onboarding đã hủy.")
    return ConversationHandler.END


def build_onboard_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("onboard", start_onboard)],
        states={
            OB_CAP_DOMAIN:       [MessageHandler(filters.TEXT & ~filters.COMMAND, ob_cap_domain)],
            OB_CAP_LEVEL:        [MessageHandler(filters.TEXT & ~filters.COMMAND, ob_cap_level)],
            OB_CAP_MAX:          [MessageHandler(filters.TEXT & ~filters.COMMAND, ob_cap_max)],
            OB_CAP_UNIT:         [MessageHandler(filters.TEXT & ~filters.COMMAND, ob_cap_unit)],
            OB_MORE_CAPS:        [CallbackQueryHandler(ob_more_caps)],
            OB_PHYS_ENERGY:      [CallbackQueryHandler(ob_phys_energy)],
            OB_PHYS_MOOD:        [CallbackQueryHandler(ob_phys_mood)],
            OB_PHYS_HEALTH:      [CallbackQueryHandler(ob_phys_health)],
            OB_PHYS_SLEEP:       [MessageHandler(filters.TEXT & ~filters.COMMAND, ob_phys_sleep)],
            OB_PROJECT_NAME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, ob_project_name)],
            OB_PROJECT_PROGRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ob_project_progress)],
            OB_MORE_PROJECTS:    [CallbackQueryHandler(ob_more_projects)],
            OB_MEMORY:           [MessageHandler(filters.TEXT & ~filters.COMMAND, ob_memory)],
            OB_MORE_MEMORY:      [CallbackQueryHandler(ob_more_memory)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )
