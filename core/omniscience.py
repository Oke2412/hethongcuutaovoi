import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from db.database import AsyncSessionLocal
from db.models import User, PhysicalStatus, CapabilityLog, WorkProject, SystemQuest, MessageLog
from datetime import datetime

logger = logging.getLogger(__name__)

async def get_omniscient_state(user_id: int) -> str:
    """Gom toàn bộ trạng thái của User (Toàn Tri) để bơm vào Prompt."""
    async with AsyncSessionLocal() as session:
        # 1. Thông tin User
        user = await session.get(User, user_id)
        if not user:
            return "[Không tìm thấy Hồ sơ Người dùng]"
            
        # 2. Thể trạng gần nhất
        stmt_phys = select(PhysicalStatus).where(PhysicalStatus.user_id == user_id).order_by(PhysicalStatus.id.desc()).limit(1)
        phys_res = await session.execute(stmt_phys)
        phys = phys_res.scalars().first()
        
        # 3. Kỹ năng
        stmt_cap = select(CapabilityLog).where(CapabilityLog.user_id == user_id)
        caps = (await session.execute(stmt_cap)).scalars().all()
        
        # 4. Dự án đang chạy
        stmt_proj = select(WorkProject).where(WorkProject.user_id == user_id, WorkProject.progress_percent < 100)
        projs = (await session.execute(stmt_proj)).scalars().all()
        
        # 5. Quest đang treo
        stmt_quest = select(SystemQuest).where(SystemQuest.user_id == user_id, SystemQuest.status == "pending")
        quests = (await session.execute(stmt_quest)).scalars().all()
        
        # 6. Lịch sử 5 tin nhắn gần nhất
        stmt_msg = select(MessageLog).where(MessageLog.user_id == user_id).order_by(MessageLog.id.desc()).limit(5)
        msgs = reversed((await session.execute(stmt_msg)).scalars().all())

    # Build the string
    state = "=== TRẠNG THÁI TOÀN TRI (OMNISCIENCE STATE) ===\n"
    state += f"Thời gian hiện tại: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    state += f"Tín chỉ (Credits): {user.credits if user else 0}\n"
    state += f"Danh hiệu: {user.titles if user and user.titles else 'Không có'}\n"
    state += f"Buff/Debuff hiện tại: {user.active_buff if user and user.active_buff else 'Không có'}\n"
    
    if phys:
        state += f"\n[THỂ TRẠNG]\nNăng lượng: {phys.energy}/10 | Tâm trạng: {phys.mood}/10 | Sức khỏe: {phys.health}/10\n"
        
    if caps:
        state += "\n[CÂY KỸ NĂNG]\n"
        for c in caps:
            state += f"- {c.domain}: Lv.{c.current_level} (EXP: {c.exp}) {c.unit}\n"
            
    if projs:
        state += "\n[DỰ ÁN ĐANG CHẠY]\n"
        for p in projs:
            state += f"- {p.name}: {p.progress_percent}%\n"
            
    if quests:
        state += "\n[NHIỆM VỤ (QUEST) ĐANG TREO]\n"
        for q in quests:
            state += f"- ID {q.id}: {q.title} ({q.description}) - Thưởng: {q.reward}\n"
            
    state += "\n[LỊCH SỬ HỘI THOẠI NGẮN HẠN (SLIDING WINDOW)]\n"
    for m in msgs:
        role_str = "Master" if m.role == "user" else "Raphael"
        state += f"{role_str}: {m.content}\n"
        
    state += "===============================================\n"
    return state

async def log_message(user_id: int, role: str, content: str):
    """Lưu tin nhắn vào Short-term sliding window."""
    async with AsyncSessionLocal() as session:
        msg = MessageLog(user_id=user_id, role=role, content=content)
        session.add(msg)
        await session.commit()

async def get_mini_context(user_id: int) -> str:
    """~60 tokens. For LLM context injection."""
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        
        stmt_phys = select(PhysicalStatus).where(PhysicalStatus.user_id == user_id).order_by(PhysicalStatus.id.desc()).limit(1)
        phys = (await session.execute(stmt_phys)).scalars().first()
        
        stmt_cap = select(CapabilityLog).where(CapabilityLog.user_id == user_id)
        caps = (await session.execute(stmt_cap)).scalars().all()
        
        stmt_proj = select(WorkProject).where(WorkProject.user_id == user_id, WorkProject.progress_percent < 100)
        projs = (await session.execute(stmt_proj)).scalars().all()
        
        stmt_quest = select(SystemQuest).where(SystemQuest.user_id == user_id, SystemQuest.status == "pending")
        quests = (await session.execute(stmt_quest)).scalars().all()
        
    e = phys.energy if phys else "?"
    m = phys.mood if phys else "?"
    h = phys.health if phys else "?"
    c = user.credits if user else 0
    
    cap_str = ",".join([f"{c.domain} Lv{c.current_level}" for c in caps])
    proj_str = ",".join([f"{p.name}({p.progress_percent}%)" for p in projs])
    quest_str = ",".join([f"ID{q.id}:{q.title}" for q in quests])
    
    from datetime import datetime, timezone, timedelta
    vn_tz = timezone(timedelta(hours=7))
    now_str = datetime.now(vn_tz).strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        from bot.handlers.location import _location_state
        loc_data = _location_state.get(user_id)
        hex_id = loc_data["hex"] if loc_data else "Unknown"
    except ImportError:
        hex_id = "Unknown"
    
    return f"[Time: {now_str}] [Location H3: {hex_id}] | E:{e} M:{m} H:{h} | Credits:{c} | Skills:{cap_str} | Projects:{proj_str} | Quests:{quest_str}"

