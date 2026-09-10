from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_id: int = Field(unique=True, index=True)
    name: str
    username: Optional[str] = None
    credits: float = Field(default=0.0)
    titles: str = Field(default="")
    active_buff: str = Field(default="")
    buff_expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CapabilityLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    domain: str
    current_level: float
    exp: float = 0.0
    max_ever: float
    unit: str = ""
    notes: str = ""
    h3_index: Optional[str] = None
    recorded_at: datetime = Field(default_factory=datetime.utcnow)


class PhysicalStatus(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    energy: int
    mood: int
    health: int
    sleep_hours: float = 0.0
    notes: str = ""
    h3_index: Optional[str] = None
    recorded_at: datetime = Field(default_factory=datetime.utcnow)


class WorkProject(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str
    description: str = ""
    progress_percent: int = 0
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WorkLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="workproject.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    progress_delta: int = 0
    notes: str = ""
    h3_index: Optional[str] = None
    logged_at: datetime = Field(default_factory=datetime.utcnow)


class Memory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    content: str
    tags: str = ""
    importance: int = 5
    h3_index: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Reminder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    content: str
    next_remind_at: datetime
    interval_days: float = 1.0
    repetitions: int = 0
    easiness: float = 2.5
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SystemQuest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    parent_quest_id: Optional[int] = Field(default=None, foreign_key="systemquest.id", index=True)
    title: str
    description: str = ""
    reward: str = ""
    penalty: str = ""
    status: str = "pending"
    h3_index: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class MessageLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    role: str = Field(description="user or assistant")
    content: str
    h3_index: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SpatialState(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, unique=True)
    last_lat: float
    last_lon: float
    last_ping_time: datetime
    current_state: str = Field(default="UNKNOWN")
    state_start_time: datetime = Field(default_factory=datetime.utcnow)
    current_waypoint: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LifeState(SQLModel, table=True):
    """Snapshot trang thai y thuc tai mot giai doan cuoc doi."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    period: str
    snapshot_at: datetime
    active_tasks: str = ""
    unfinished: str = ""
    relationships: str = ""
    dominant_thought: str = ""
    fears_active: str = ""
    energy: int = 5
    mood: int = 5
    financial_stress: str = "none"
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
