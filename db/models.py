from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(SQLModel, table=True):
    """Telegram user registered in the system."""
    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_id: int = Field(unique=True, index=True)
    name: str
    username: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Capability tracking  �  "Current Max" per domain
# ---------------------------------------------------------------------------

class CapabilityLog(SQLModel, table=True):
    """Snapshot of user capability in a given domain."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    domain: str          # e.g. "coding", "fitness", "focus", "reading"
    current_level: float # subjective 1-10 or objective metric
    max_ever: float      # personal record for this domain
    unit: str = ""       # e.g. "push-ups", "pages/day", "hours of focus"
    notes: str = ""
    recorded_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Physical & mental status
# ---------------------------------------------------------------------------

class PhysicalStatus(SQLModel, table=True):
    """Daily/on-demand status check-in."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    energy: int          # 1-10
    mood: int            # 1-10
    health: int          # 1-10  (physical)
    sleep_hours: float = 0.0
    notes: str = ""
    recorded_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Work progress
# ---------------------------------------------------------------------------

class WorkProject(SQLModel, table=True):
    """A long-running project being tracked."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str
    description: str = ""
    progress_percent: int = 0   # 0-100
    status: str = "active"      # active | paused | done
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WorkLog(SQLModel, table=True):
    """Log entry for a project update."""
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="workproject.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    progress_delta: int = 0     # how many % added this session
    notes: str = ""
    logged_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Long-term memory
# ---------------------------------------------------------------------------

class Memory(SQLModel, table=True):
    """A piece of information the system should remember about the user."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    content: str
    tags: str = ""   # comma-separated tags
    importance: int = 5    # 1-10, higher = more likely to include in context
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Reminders  �  SM-2 spaced repetition
# ---------------------------------------------------------------------------

class Reminder(SQLModel, table=True):
    """A reminder item managed with SM-2 algorithm."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    content: str
    next_remind_at: datetime
    interval_days: float = 1.0  # SM-2 interval
    repetitions: int = 0        # times successfully recalled
    easiness: float = 2.5       # SM-2 easiness factor
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
