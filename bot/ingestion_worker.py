import asyncio
import logging
import os
import json
from sqlalchemy import select
from db.database import AsyncSessionLocal
from db.models import MessageLog
from openai import AsyncOpenAI
from config import settings

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=settings.siliconflow_api_key, base_url='https://api.siliconflow.com/v1')

LAST_ID_FILE = "data/last_ingest.json"

def load_last_ids():
    if os.path.exists(LAST_ID_FILE):
        try:
            with open(LAST_ID_FILE, "r") as f:
                return {int(k): v for k, v in json.load(f).items()}
        except Exception:
            pass
    return {}

def save_last_ids(data):
    with open(LAST_ID_FILE, "w") as f:
        json.dump(data, f)

last_processed_ids = load_last_ids()

async def micro_router_check(buffer_text: str) -> bool:
    prompt = f"""Analyze the user's conversation below. Does it contain any significant personal events, psychological shifts, goals, or causal relationships worth storing long-term in the Knowledge Graph?

CRITICAL RULE:
If the user is testing the bot, debugging, or just sending short meaningless phrases (e.g., 'alo', 'test', 'ok', etc.), you MUST answer NO. Only save genuine data about their life, habits, or psychology.

ANSWER WITH EXACTLY ONE WORD: YES or NO. No explanations.

Conversation:
{buffer_text}"""
    
    resp = await client.chat.completions.create(
        model="deepseek-ai/deepseek-v4.1-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=500
    )
    res = resp.choices[0].message.content.strip().upper()
    return "YES" in res

async def trigger_heavy_ingestion(text: str):
    import subprocess
    import os
    os.makedirs("scratch", exist_ok=True)
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
                            last_processed_ids[uid] = messages[-1].id
                            save_last_ids(last_processed_ids)
                        else:
                            logger.info(f"Micro-Router returned NO. Discarding buffer.")
                            last_processed_ids[uid] = messages[-1].id
                            save_last_ids(last_processed_ids)
        except Exception as e:
            logger.error(f"Ingestion Worker Error: {e}")
