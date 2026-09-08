import math
from datetime import datetime
import logging
from sqlalchemy.future import select
from db.database import AsyncSessionLocal
from db.models import SpatialState

logger = logging.getLogger(__name__)

# Constants
STATIONARY_RADIUS_KM = 0.05  # 50 met
MIN_STATIONARY_MINUTES = 3.0 # Dừng ít nhất 3 phút thì tính là STATIONARY (loại trừ chờ đèn đỏ ngắn)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Tính khoảng cách giữa 2 tọa độ GPS (bằng km)"""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

async def get_or_create_spatial_state(session, user_id: int, lat: float, lon: float) -> SpatialState:
    stmt = select(SpatialState).where(SpatialState.user_id == user_id)
    result = await session.execute(stmt)
    state = result.scalars().first()
    
    if not state:
        state = SpatialState(
            user_id=user_id,
            last_lat=lat,
            last_lon=lon,
            last_ping_time=datetime.utcnow(),
            current_state="UNKNOWN",
            state_start_time=datetime.utcnow()
        )
        session.add(state)
        await session.commit()
        await session.refresh(state)
    return state

async def process_location(user_id: int, lat: float, lon: float) -> str:
    """
    Nhận tọa độ mới, phân tích vận tốc & trạng thái.
    Trả về event (nếu có) để kích hoạt Side Quest.
    """
    now = datetime.utcnow()
    event = None

    async with AsyncSessionLocal() as session:
        state = await get_or_create_spatial_state(session, user_id, lat, lon)
        
        if state.current_state == "UNKNOWN":
            state.current_state = "STATIONARY"
            state.last_lat = lat
            state.last_lon = lon
            state.last_ping_time = now
            state.state_start_time = now
            await session.commit()
            return ""

        distance_km = haversine_distance(state.last_lat, state.last_lon, lat, lon)
        time_diff_hours = (now - state.last_ping_time).total_seconds() / 3600.0
        
        if time_diff_hours <= 0:
            return ""

        speed_kmh = distance_km / time_diff_hours
        new_state = state.current_state
        
        if speed_kmh > 5.0 or distance_km > STATIONARY_RADIUS_KM:
            new_state = "TRANSITING"

        if new_state == "TRANSITING":
            if state.current_state == "STATIONARY":
                event = "STARTED_MOVING"
                
            state.current_state = "TRANSITING"
            state.state_start_time = now
            
        if speed_kmh <= 5.0 and distance_km <= STATIONARY_RADIUS_KM:
            time_stopped_mins = (now - state.state_start_time).total_seconds() / 60.0
            
            if state.current_state == "TRANSITING":
                state.current_state = "WAITING"
                state.state_start_time = now
                
            elif state.current_state == "WAITING":
                if time_stopped_mins >= MIN_STATIONARY_MINUTES:
                    state.current_state = "STATIONARY"
                    event = "ARRIVED_WAYPOINT"

        state.last_lat = lat
        state.last_lon = lon
        state.last_ping_time = now
        await session.commit()
        
    return event or ""
