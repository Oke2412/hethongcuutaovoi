import logging
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Create all tables on startup."""
    # Import models so SQLModel registers them
    from db import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        
        # Setup FTS5 for messagelog
        try:
            from sqlalchemy import text
            await conn.execute(text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS messagelog_fts 
                USING fts5(id UNINDEXED, content, sender);
            """))
            # Trigger for insert
            await conn.execute(text("""
                CREATE TRIGGER IF NOT EXISTS messagelog_ai AFTER INSERT ON messagelog
                BEGIN
                    INSERT INTO messagelog_fts(id, content, sender) 
                    VALUES (new.id, new.content, new.sender);
                END;
            """))
            # Trigger for delete
            await conn.execute(text("""
                CREATE TRIGGER IF NOT EXISTS messagelog_ad AFTER DELETE ON messagelog
                BEGIN
                    DELETE FROM messagelog_fts WHERE id = old.id;
                END;
            """))
            # Trigger for update
            await conn.execute(text("""
                CREATE TRIGGER IF NOT EXISTS messagelog_au AFTER UPDATE ON messagelog
                BEGIN
                    DELETE FROM messagelog_fts WHERE id = old.id;
                    INSERT INTO messagelog_fts(id, content, sender) 
                    VALUES (new.id, new.content, new.sender);
                END;
            """))
        except Exception as e:
            logger.warning(f"Could not setup FTS5: {e}")
            
    logger.info("Database initialised.")


async def get_session() -> AsyncSession:  # type: ignore[override]
    """Dependency / context manager for a DB session."""
    async with AsyncSessionLocal() as session:
        yield session
