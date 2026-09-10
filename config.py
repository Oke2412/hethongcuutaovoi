from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Telegram
    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")

    # LLM
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    qwen_api_key: str = Field(default="", alias="QWEN_API_KEY")
    reranker_api_url: str = Field(default="https://openrouter.ai/api/v1/rerank", alias="RERANKER_API_URL")
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

    # Neo4j and H3
    neo4j_uri: str = Field(default="neo4j://neo4j:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="password", alias="NEO4J_PASSWORD")
    h3_resolution: int = Field(default=9, alias="H3_RESOLUTION")

    # LLM behavior
    llm_system_persona: str = Field(default="strict", alias="LLM_SYSTEM_PERSONA")

    model_config = {"env_file": ".env", "populate_by_name": True}


settings = Settings()
