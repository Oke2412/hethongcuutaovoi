from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Telegram
    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")

    # LLM
    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/amazing_nobel.db",
        alias="DATABASE_URL",
    )

    # Scheduler
    reminder_check_interval_minutes: int = Field(
        default=5, alias="REMINDER_CHECK_INTERVAL_MINUTES"
    )
    daily_checkin_hour: int = Field(default=21, alias="DAILY_CHECKIN_HOUR")
    daily_checkin_minute: int = Field(default=0, alias="DAILY_CHECKIN_MINUTE")

    # LLM behavior
    llm_system_persona: str = Field(default="strict", alias="LLM_SYSTEM_PERSONA")

    model_config = {"env_file": ".env", "populate_by_name": True}


settings = Settings()
