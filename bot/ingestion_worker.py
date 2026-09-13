import asyncio
import logging
from sqlalchemy import select
from db.database import AsyncSessionLocal
from db.models import MessageLog
from openai import AsyncOpenAI
from config import settings

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=settings.siliconflow_api_key, base_url='https://api.siliconflow.com/v1')

last_processed_ids = {}

async def micro_router_check(buffer_text: str) -> bool:
    prompt = f"""Đọc đoạn hội thoại sau của người dùng. Có bất kỳ sự kiện cá nhân, thay đổi tâm lý, mục tiêu, hoặc mối quan hệ nhân quả nào đáng để ghi nhớ dài hạn vào Knowledge Graph không? 
CHỈ TRẢ LỜI ĐÚNG 1 CHỮ: YES hoặc NO. Không giải thích.

Hội thoại:
{buffer_text}"""
    
    resp = await client.chat.completions.create(
        model="deepseek-ai/deepseek-v4.1-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=5
    )
    res = resp.choices[0].message.content.strip().upper()
    return "YES" in res

async def trigger_heavy_ingestion(text: str):
    import subprocess
    with open("scratch/temp_ingest.txt", "w", encoding="utf-8") as f:
        f.write(text)
    subprocess.Popen(["python", "scripts/ingest_text.py", "scratch/temp_ingest.txt"])
    logger.info("Triggered heavy GraphRAG ingestion for buffer.")

async def ingestion_loop():
    logger.info("Ingestion Worker started.")
    while True:
        await asyncio.sleep(60) # Check every 60 seconds
        try:
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(MessageLog.user_id).distinct())
                users = res.scalars().all()
                
                for uid in users:
                    last_id = last_processed_ids.get(uid, 0)
                    msg_res = await session.execute(
                        select(MessageLog).where(MessageLog.user_id == uid, MessageLog.id > last_id).order_by(MessageLog.id.asc())
                    )
                    messages = msg_res.scalars().all()
                    
                    if not messages:
                        continue
                        
                    buffer_text = "\n".join([f"{m.role}: {m.content}" for m in messages])
                    # Volume trigger: 5 messages or 500 chars
                    if len(messages) >= 5 or len(buffer_text) >= 500:
                        logger.info(f"Buffer full for user {uid} (Msgs: {len(messages)}, Chars: {len(buffer_text)}). Running Micro-Router...")
                        
                        is_valuable = await micro_router_check(buffer_text)
                        
                        if is_valuable:
                            logger.info(f"Micro-Router returned YES. Spawning ingestion...")
                            await trigger_heavy_ingestion(buffer_text)
                        else:
                            logger.info(f"Micro-Router returned NO. Discarding buffer.")
                        
                        last_processed_ids[uid] = messages[-1].id
        except Exception as e:
            logger.error(f"Ingestion Worker Error: {e}")
