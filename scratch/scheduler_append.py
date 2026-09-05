
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
