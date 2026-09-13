import asyncio
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import AsyncSessionLocal
from db.models import MessageLog

async def main():
    async with AsyncSessionLocal() as session:
        msgs = [
            MessageLog(user_id=999, role="user", content="Nay tao vừa nhận một task cực khó từ sếp về việc tối ưu hóa Robotic Arm. Hơi mệt nhưng phải ráng.", timestamp=datetime.utcnow()),
            MessageLog(user_id=999, role="assistant", content="《Báo cáo》: Đã ghi nhận LifeEvent mới: Nhận task Robotic Arm. Mức năng lượng giảm.", timestamp=datetime.utcnow()),
            MessageLog(user_id=999, role="user", content="Thật ra tao đang bị quá tải, ngày nào cũng thức đến 3h sáng để code. Cảm giác chán nản vãi.", timestamp=datetime.utcnow()),
            MessageLog(user_id=999, role="assistant", content="《Báo cáo》: Phát hiện thói quen Thức khuya (đến 3h sáng). Kích hoạt cảm xúc: Chán nản.", timestamp=datetime.utcnow()),
            MessageLog(user_id=999, role="user", content="Thay vì ngồi code tao lại mở TopTop lướt 2 tiếng rồi. Chắc là để trốn tránh áp lực. Bực mình bản thân ghê.", timestamp=datetime.utcnow())
        ]
        session.add_all(msgs)
        await session.commit()
        print("Đã giả lập 5 tin nhắn vào SQLite (user_id=999).")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
