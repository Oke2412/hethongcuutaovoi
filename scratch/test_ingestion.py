import asyncio
import logging
from sqlalchemy import select
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import AsyncSessionLocal
from db.models import MessageLog
from openai import AsyncOpenAI
from config import settings

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=settings.siliconflow_api_key, base_url='https://api.siliconflow.com/v1')

async def micro_router_check(buffer_text: str) -> bool:
    prompt = f"""Đọc đoạn hội thoại sau của người dùng. Có bất kỳ sự kiện cá nhân, thay đổi tâm lý, mục tiêu, hoặc mối quan hệ nhân quả nào đáng để ghi nhớ dài hạn vào Knowledge Graph không? 
CHỈ TRẢ LỜI ĐÚNG 1 CHỮ: YES hoặc NO. Không giải thích.

Hội thoại:
{buffer_text}"""
    
    resp = await client.chat.completions.create(
        model="deepseek-ai/deepseek-v4.1-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=500
    )
    res = resp.choices[0].message.content.strip().upper()
    print(f"[MICRO-ROUTER RESULT]: {res}")
    return "YES" in res

async def trigger_heavy_ingestion(text: str):
    import subprocess
    with open("scratch/temp_ingest.txt", "w", encoding="utf-8") as f:
        f.write(text)
    
    print("[SPAWNING GRAPH INGESTION]")
    proc = subprocess.Popen(["python", "scripts/ingest_text.py", "scratch/temp_ingest.txt"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
    stdout, stderr = proc.communicate()
    print("[GRAPH INGESTION OUTPUT]")
    print(stdout)
    if stderr:
        print("[GRAPH INGESTION ERRORS]")
        print(stderr)

async def test_run():
    async with AsyncSessionLocal() as session:
        msg_res = await session.execute(
            select(MessageLog).where(MessageLog.user_id == 999).order_by(MessageLog.id.asc())
        )
        messages = msg_res.scalars().all()
        
        if not messages:
            print("Khong co tin nhan")
            return
            
        buffer_text = "\n".join([f"{m.role}: {m.content}" for m in messages])
        print(f"--- BUFFER ({len(messages)} messages) ---\n{buffer_text}\n-------------------")
        
        is_valuable = await micro_router_check(buffer_text)
        if is_valuable:
            await trigger_heavy_ingestion(buffer_text)

if __name__ == "__main__":
    # Windows fix
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_run())
