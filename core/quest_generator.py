import json
import logging
from datetime import datetime
import google.generativeai as genai
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
            
        # Cancel all old pending quests to refresh
        old_quests = await session.execute(
            select(SystemQuest).where(SystemQuest.user_id == user.id, SystemQuest.status == "pending")
        )
        for q in old_quests.scalars().all():
            q.status = "cancelled"
            
        context = await build_user_context(session, user)
        prompt = PROMPT_QUEST + "\n\n--- CONTEXT ---\n" + context

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(
            model_name="gemini-3.8-flash",
            generation_config={"response_mime_type": "application/json"}
        )
        
        try:
            response = model.generate_content(prompt)
            quests_data = json.loads(response.text.strip())
            
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
