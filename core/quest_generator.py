import json
import logging
import asyncio
from datetime import datetime


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from config import settings
from db.database import AsyncSessionLocal
from db.models import User, SystemQuest
from core.memory import build_user_context

logger = logging.getLogger(__name__)

PROMPT_QUEST = """Đóng vai trò là Raphael (Thần Trí Hạch). 
Phân tích lịch trình, thể trạng, tiến độ dự án của người dùng và sinh ra 1 hoặc 2 [Nhiệm vụ Hệ thống] cực kỳ quan trọng và phù hợp cho hôm nay.
Nếu người dùng đang kiệt sức (energy thấp), nhiệm vụ nên là nghỉ ngơi, ngủ bù.
Nếu người dùng đang khỏe, nhiệm vụ có thể là tiếp tục dự án đang dang dở.
Kèm theo Phần thưởng (thời gian nghỉ ngơi, chơi game, ăn uống) tương xứng.

Bạn PHẢI trả về đúng định dạng JSON sau:
[
  {
    "title": "Tên nhiệm vụ ngắn gọn",
    "description": "Lý do vì sao phải làm nhiệm vụ này",
    "reward": "Phần thưởng khi hoàn thành",
    "penalty": "Hình phạt nếu thất bại (nếu có)"
  }
]
Không trả về bất kỳ markdown hay text nào khác.
"""

async def generate_and_save_quest(user_id: int):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            return None
            
        old_quests = await session.execute(
            select(SystemQuest).where(SystemQuest.user_id == user.id, SystemQuest.status == "pending")
        )
        for q in old_quests.scalars().all():
            q.status = "cancelled"
            
        context = await build_user_context(session, user)
        prompt = PROMPT_QUEST + "\n\n--- CONTEXT ---\n" + context

        from core.llm import _get_llm_client
        client = _get_llm_client()
        
        from config import settings
        try:
            response = await client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[
                    {"role": "system", "content": "Output ONLY a valid JSON array. No markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            text_resp = response.choices[0].message.content.strip()
            if text_resp.startswith("```json"):
                text_resp = text_resp.replace("```json", "").replace("```", "").strip()
            quests_data = json.loads(text_resp)
            
            for qdata in quests_data:
                q = SystemQuest(
                    user_id=user.id,
                    title=qdata.get("title", "Nhiệm vụ"),
                    description=qdata.get("description", ""),
                    reward=qdata.get("reward", ""),
                    penalty=qdata.get("penalty", ""),
                    status="pending"
                )
                session.add(q)
                
            await session.commit()
            return quests_data
        except Exception as exc:
            logger.error(f"Failed to generate quests: {exc}", exc_info=True)
            return None
