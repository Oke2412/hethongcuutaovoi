import asyncio
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import AsyncSessionLocal
from db.models import MessageLog
from sqlalchemy import delete

async def main():
    async with AsyncSessionLocal() as session:
        # Clear previous
        await session.execute(delete(MessageLog).where(MessageLog.user_id == 999))
        await session.commit()
        
        # Simulate Vision Bridge Scenario
        msgs = [
            MessageLog(user_id=999, role="user", content="[Master vừa gửi một bức ảnh có ly cafe và phong cảnh Đà Lạt]", timestamp=datetime.utcnow()),
            MessageLog(user_id=999, role="assistant", content="《Báo cáo》: Xác nhận Master đang ở quán cafe tại Đà Lạt. Chuyến đi healing này sẽ giúp phục hồi HP và làm dịu áp lực từ dự án đợt trước.", timestamp=datetime.utcnow()),
            MessageLog(user_id=999, role="user", content="Đúng rồi, mát mẻ quá. Tao thấy khỏe hơn hẳn.", timestamp=datetime.utcnow()),
            MessageLog(user_id=999, role="assistant", content="《Xác nhận》: Mức năng lượng và cảm xúc đã chuyển sang trạng thái Tích cực (Khôi phục).", timestamp=datetime.utcnow())
        ]
        session.add_all(msgs)
        await session.commit()
        print("Đã giả lập hội thoại Vision (user_id=999).")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
