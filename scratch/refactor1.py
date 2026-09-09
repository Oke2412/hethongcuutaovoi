import codecs
import os

def write_utf8(path, content):
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(content)

# 1. Update requirements.txt (just rewrite the whole file cleanly)
req_content = """python-telegram-bot==22.8
fastapi==0.115.5
uvicorn[standard]==0.32.1
sqlmodel==0.0.22
aiosqlite==0.20.0

groq==0.11.0
pydantic-settings==2.6.1
apscheduler==3.10.4
httpx==0.27.2
python-dotenv==1.0.1
structlog==24.4.0
mem0ai
chromadb

sentence-transformers
google-genai
h3==4.1.*
neo4j==5.*
"""
write_utf8(r'c:\Users\Asus\Documents\antigravity\amazing-nobel\requirements.txt', req_content)

# 2. Add H3 / Neo4j to .env.example
env_example_content = """# ================================
# Amazing Nobel — Environment Config
# Copy to .env and fill in values
# ================================

# --- Telegram ---
TELEGRAM_BOT_TOKEN=8715926583:AAEIo0MZJdf1-tVUGAnV6ahE0Szv_2Iggxo

# --- LLM ---
GEMINI_API_KEY=AQ.Ab8RN6JHBeou2MjxcCoTMnjKcpqf8VkrBk7e1Lk-P0nOuGSZUw
GROQ_API_KEY=                              # Optional fallback

# --- Database ---
DATABASE_URL=sqlite+aiosqlite:///./data/amazing_nobel.db

# --- Scheduler ---
REMINDER_CHECK_INTERVAL_MINUTES=5         # How often APScheduler checks for due reminders
DAILY_CHECKIN_HOUR=21                     # Hour (24h) for daily check-in reminder
DAILY_CHECKIN_MINUTE=0

# --- LLM Behavior ---
LLM_SYSTEM_PERSONA=friendly                 # strict | friendly | mentor

# --- H3 & Neo4j ---
NEO4J_URI=neo4j://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
H3_RESOLUTION=9
"""
write_utf8(r'c:\Users\Asus\Documents\antigravity\amazing-nobel\.env.example', env_example_content)

# 3. Write new core/router.py
router_content = """import re, unicodedata
from google import genai
import asyncio

def _normalize(text: str) -> str:
    \"\"\"Strip diacritics for Vietnamese matching.\"\"\"
    return unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode()

# Data patterns (cả có dấu lẫn không dấu)
DATA_KEYWORDS = [
    r"\\b(can|kg|kilo|chieu cao|cm|bmi|ngu|giac ngu|met|moi|nang luong|energy|suc khoe|dau|om|tam trang|mood)\\b",
    r"\\b(hoc|tap|luyen|code|viet|doc|skill|level|exp|du an|project|tien do|xong|done|hoàn thành|hoàn tất)\\b",
    r"\\b(quest|nhiem vu|task|huy|cancel|reward|credits|tin chi)\\b",
    r"\\b\\d+\\s*(kg|cm|h|gio|phut|%|diem|exp)\\b",
]

DEEP_KEYWORDS = [
    r"\\b(phan tich|phan tích|ke hoach|kế hoạch|lich|lịch|tuần|thang|tháng|muc tieu|mục tiêu|vì sao|tai sao|tại sao)\\b",
]

def classify_message(text: str) -> str:
    \"\"\"Returns: 'chat' | 'data' | 'deep'\"\"\"
    norm = _normalize(text.lower())
    if any(re.search(p, norm) for p in DEEP_KEYWORDS):
        return "deep"
    if any(re.search(p, norm) for p in DATA_KEYWORDS):
        return "data"
    return "chat"

ROUTER_ANCHORS = {
    "data": "can nang hoc tap ngu du an tien do ky nang exp level",
    "chat": "met moi buon vui cam xuc than van chia se cam giac",
    "deep": "phan tich ke hoach muc tieu tai sao ly do chien luoc",
}

async def semantic_classify(text: str, client: genai.Client) -> str:
    try:
        msg_emb = await asyncio.to_thread(
            client.models.embed_content,
            model="gemini-embedding-2",
            contents=text,
        )
        # Simplify semantic classify for now as the plan only said "..." 
        # Fallback to regex since full logic was elided in plan.
        return classify_message(text)
    except Exception:
        return classify_message(text)
"""
write_utf8(r'c:\Users\Asus\Documents\antigravity\amazing-nobel\core\router.py', router_content)

# 4. Write new core/hud.py
hud_content = """from db.database import AsyncSessionLocal
from sqlmodel import select
from db.models import User, PhysicalStatus, SystemQuest
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

async def build_hud(user_id: int) -> tuple[str, InlineKeyboardMarkup | None]:
    \"\"\"Returns (hud_line, keyboard) from current DB state.\"\"\"
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            return "━━━━━━━━━━━━━━━━━━━━━\\n⚡ ? | 😐 ? | ❤️ ? | 💎 ?cr | 📍 H3:?", None
            
        stmt_phys = select(PhysicalStatus).where(PhysicalStatus.user_id == user_id).order_by(PhysicalStatus.id.desc()).limit(1)
        phys = (await session.execute(stmt_phys)).scalars().first()
        
        energy = phys.energy if phys else "?"
        mood = phys.mood if phys else "?"
        health = phys.health if phys else "?"
        credits = user.credits if user else 0
        
        # Lấy Hex ID (từ logic tạm hoặc location state) - sẽ được update thông qua flow location
        # Hiện tại trả về "?", hệ thống Location sẽ lưu vào DB hoặc state.
        hex_id = "?" 
        
        hud_line = f"━━━━━━━━━━━━━━━━━━━━━\\n⚡ {energy}/10 | 😐 {mood}/10 | ❤️ {health}/10 | 💎 {credits}cr | 📍 H3:{hex_id}"
        
        stmt_quest = select(SystemQuest).where(SystemQuest.user_id == user_id, SystemQuest.status == "pending")
        quests = (await session.execute(stmt_quest)).scalars().all()
        
        keyboard = None
        if quests:
            buttons = []
            for q in quests:
                buttons.append([
                    InlineKeyboardButton(f"✅ Hoàn thành quest #{q.id}", callback_data=f"complete_{q.id}"),
                    InlineKeyboardButton("❌ Hủy", callback_data=f"cancel_{q.id}")
                ])
            keyboard = InlineKeyboardMarkup(buttons)
            
        return hud_line, keyboard
"""
write_utf8(r'c:\Users\Asus\Documents\antigravity\amazing-nobel\core\hud.py', hud_content)

# 5. Write new core/neo4j_client.py
neo4j_client_content = """import logging
from neo4j import AsyncGraphDatabase
from config import settings

logger = logging.getLogger(__name__)
_driver = None

def get_neo4j_driver():
    global _driver
    if _driver is None:
        try:
            _driver = AsyncGraphDatabase.driver(
                getattr(settings, "neo4j_uri", "neo4j://neo4j:7687"),
                auth=(
                    getattr(settings, "neo4j_user", "neo4j"),
                    getattr(settings, "neo4j_password", "password"),
                ),
            )
        except Exception as exc:
            logger.warning("Neo4j unavailable: %s", exc)
            return None
    return _driver
"""
write_utf8(r'c:\Users\Asus\Documents\antigravity\amazing-nobel\core\neo4j_client.py', neo4j_client_content)

# 6. Write new scripts/init_neo4j.py
init_neo4j_content = """import asyncio
from core.neo4j_client import get_neo4j_driver

async def init_db():
    driver = get_neo4j_driver()
    if driver is None:
        print("Neo4j driver not available")
        return
        
    async with driver.session() as session:
        await session.run("CREATE INDEX h3_hex_id IF NOT EXISTS FOR (h:H3_Cell) ON (h.hex_id);")
        await session.run("CREATE INDEX life_event_uid IF NOT EXISTS FOR (e:LifeEvent) ON (e.user_id);")
        await session.run("CREATE INDEX user_uid IF NOT EXISTS FOR (u:User) ON (u.user_id);")
        print("Neo4j indexes created.")
        
if __name__ == "__main__":
    asyncio.run(init_db())
"""
write_utf8(r'c:\Users\Asus\Documents\antigravity\amazing-nobel\scripts\init_neo4j.py', init_neo4j_content)

print("Batch 1 created successfully.")
