"""
scripts/brain_dump_import.py
Chay: python scripts/brain_dump_import.py brain_dump.json <telegram_id>

Import toan bo du lieu tu brain_dump.json vao:
  - SQLite (Memory, CapabilityLog, PhysicalStatus, WorkProject, LifeState)
  - ChromaDB via Mem0 (vector search)
  - Neo4j (LifeEvent + LifeState nodes + causal edges)

Idempotent: chay nhieu lan khong bi duplicate (dung content hash lam key).
"""

import sys
import json
import asyncio
import hashlib
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _parse_dt(s: str) -> datetime:
    """Parse ISO datetime string, fallback to now."""
    if not s:
        return datetime.utcnow()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y-%m"):
        try:
            return datetime.strptime(s[:len(fmt) + (2 if "T" in fmt else 0)], fmt)
        except ValueError:
            continue
    return datetime.utcnow()


async def get_or_create_user(session, telegram_id: int, name: str):
    from sqlmodel import select
    from db.models import User
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalars().first()
    if not user:
        user = User(telegram_id=telegram_id, name=name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info("Created user id=%d name=%s", user.id, user.name)
    else:
        logger.info("Found existing user id=%d", user.id)
    return user


async def import_memories(session, user_id: int, memories: list, mem0_client):
    from sqlmodel import select
    from db.models import Memory
    imported = 0
    for m in memories:
        content = m.get("content", "").strip()
        if not content:
            continue
        # Idempotency: check by content hash
        tags = m.get("tags", "")
        importance = int(m.get("importance", 5))
        created_at = _parse_dt(m.get("created_at", ""))
        # Check duplicate
        stmt = select(Memory).where(Memory.user_id == user_id, Memory.content == content)
        exists = (await session.execute(stmt)).scalars().first()
        if exists:
            continue
        row = Memory(user_id=user_id, content=content, tags=tags,
                     importance=importance, created_at=created_at)
        session.add(row)
        # Push to Mem0 vector store
        if mem0_client:
            try:
                mem0_client.add(
                    messages=[{"role": "user", "content": content}],
                    user_id=str(user_id),
                    metadata={"tags": tags, "importance": importance,
                              "created_at": created_at.isoformat(), "source": "brain_dump"},
                )
            except Exception as e:
                logger.warning("Mem0 add failed: %s", e)
        imported += 1
    await session.commit()
    logger.info("Memories: imported %d / %d", imported, len(memories))


async def import_capabilities(session, user_id: int, capabilities: list):
    from sqlmodel import select
    from db.models import CapabilityLog
    imported = 0
    for c in capabilities:
        domain = c.get("domain", "").strip()
        if not domain:
            continue
        # Update or create
        stmt = select(CapabilityLog).where(
            CapabilityLog.user_id == user_id, CapabilityLog.domain == domain
        )
        existing = (await session.execute(stmt)).scalars().first()
        level = float(c.get("current_level", 1.0))
        exp = float(c.get("exp", 0.0))
        max_ever = float(c.get("max_ever", level))
        if existing:
            existing.current_level = max(existing.current_level, level)
            existing.exp = max(existing.exp, exp)
            existing.max_ever = max(existing.max_ever, max_ever)
            existing.notes = c.get("notes", existing.notes)
        else:
            row = CapabilityLog(
                user_id=user_id, domain=domain, current_level=level,
                exp=exp, max_ever=max_ever,
                unit=c.get("unit", ""), notes=c.get("notes", "")
            )
            session.add(row)
            imported += 1
    await session.commit()
    logger.info("Capabilities: imported %d / %d", imported, len(capabilities))


async def import_physical_history(session, user_id: int, physical_history: list):
    from db.models import PhysicalStatus
    imported = 0
    for p in physical_history:
        notes = p.get("notes", "")
        recorded_at = _parse_dt(p.get("recorded_at", ""))
        row = PhysicalStatus(
            user_id=user_id,
            energy=int(p.get("energy", 5)),
            mood=int(p.get("mood", 5)),
            health=int(p.get("health", 5)),
            sleep_hours=float(p.get("sleep_hours", 0.0)),
            notes=notes,
            recorded_at=recorded_at,
        )
        session.add(row)
        imported += 1
    await session.commit()
    logger.info("PhysicalHistory: imported %d rows", imported)


async def import_projects(session, user_id: int, projects: list):
    from sqlmodel import select
    from db.models import WorkProject
    imported = 0
    for p in projects:
        name = p.get("name", "").strip()
        if not name:
            continue
        stmt = select(WorkProject).where(WorkProject.user_id == user_id, WorkProject.name == name)
        existing = (await session.execute(stmt)).scalars().first()
        if existing:
            existing.progress_percent = p.get("progress_percent", existing.progress_percent)
            existing.status = p.get("status", existing.status)
        else:
            row = WorkProject(
                user_id=user_id, name=name,
                description=p.get("description", ""),
                progress_percent=int(p.get("progress_percent", 0)),
                status=p.get("status", "active"),
                created_at=_parse_dt(p.get("created_at", "")),
            )
            session.add(row)
            imported += 1
    await session.commit()
    logger.info("Projects: imported %d / %d", imported, len(projects))


async def import_life_states(session, user_id: int, life_states: list, driver):
    from sqlmodel import select
    from db.models import LifeState
    imported = 0
    for s in life_states:
        period = s.get("period", "").strip()
        if not period:
            continue
        stmt = select(LifeState).where(LifeState.user_id == user_id, LifeState.period == period)
        if (await session.execute(stmt)).scalars().first():
            continue
        snapshot_at = _parse_dt(s.get("snapshot_at", ""))
        row = LifeState(
            user_id=user_id,
            period=period,
            snapshot_at=snapshot_at,
            active_tasks=json.dumps(s.get("active_tasks", []), ensure_ascii=False),
            unfinished=json.dumps(s.get("unfinished", []), ensure_ascii=False),
            relationships=json.dumps(s.get("relationships", {}), ensure_ascii=False),
            dominant_thought=s.get("dominant_thought", ""),
            fears_active=json.dumps(s.get("fears_active", []), ensure_ascii=False),
            energy=int(s.get("energy", 5)),
            mood=int(s.get("mood", 5)),
            financial_stress=s.get("financial_stress", "none"),
            notes=s.get("notes", ""),
        )
        session.add(row)
        # Neo4j StateNode
        if driver:
            try:
                async with driver.session() as neo_s:
                    await neo_s.run(
                        """
                        MERGE (u:User {id: $uid})
                        MERGE (st:LifeState {period: $period, user_id: $uid})
                        ON CREATE SET st.snapshot_at = $ts,
                                      st.energy = $energy,
                                      st.mood = $mood,
                                      st.dominant_thought = $dt,
                                      st.financial_stress = $fs,
                                      st.notes = $notes
                        MERGE (u)-[:LIVED_THROUGH]->(st)
                        """,
                        uid=user_id, period=period,
                        ts=snapshot_at.isoformat(),
                        energy=int(s.get("energy", 5)),
                        mood=int(s.get("mood", 5)),
                        dt=s.get("dominant_thought", ""),
                        fs=s.get("financial_stress", "none"),
                        notes=s.get("notes", ""),
                    )
            except Exception as e:
                logger.warning("Neo4j LifeState failed: %s", e)
        imported += 1
    await session.commit()
    logger.info("LifeStates: imported %d / %d", imported, len(life_states))


async def import_life_events(session, user_id: int, life_events: list, mem0_client, driver):
    from db.models import Memory
    imported = 0
    for e in life_events:
        desc = e.get("description", "").strip()
        if not desc:
            continue
        occurred_at = _parse_dt(e.get("occurred_at", ""))
        # Store in Memory table for text retrieval
        full_content = (
            f"[{e.get('event_type','EVENT')} | {e.get('impact','MEDIUM')}] {desc} "
            f"| Nguyên nhân: {e.get('cause','')} "
            f"| Hệ quả: {e.get('consequence','')} "
            f"| Bài học: {e.get('lesson','')} "
            f"| Cảm xúc: {e.get('emotion_at_time','')} "
            f"| E={e.get('energy_at_time',5)} M={e.get('mood_at_time',5)}"
        )
        # Mem0 vector
        if mem0_client:
            try:
                mem0_client.add(
                    messages=[{"role": "user", "content": full_content}],
                    user_id=str(user_id),
                    metadata={"source": "brain_dump_event",
                              "event_type": e.get("event_type", ""),
                              "impact": e.get("impact", ""),
                              "occurred_at": occurred_at.isoformat()},
                )
            except Exception as ex:
                logger.warning("Mem0 event add failed: %s", ex)
        # Neo4j EventNode
        if driver:
            try:
                async with driver.session() as neo_s:
                    await neo_s.run(
                        """
                        MERGE (u:User {id: $uid})
                        CREATE (ev:LifeEvent {
                            description: $desc,
                            event_type: $etype,
                            impact: $impact,
                            emotion: $emotion,
                            energy: $energy,
                            mood: $mood,
                            cause: $cause,
                            consequence: $consequence,
                            lesson: $lesson,
                            occurred_at: $ts
                        })
                        CREATE (u)-[:EXPERIENCED]->(ev)
                        """,
                        uid=user_id,
                        desc=desc,
                        etype=e.get("event_type", "EVENT"),
                        impact=e.get("impact", "MEDIUM"),
                        emotion=e.get("emotion_at_time", ""),
                        energy=int(e.get("energy_at_time", 5)),
                        mood=int(e.get("mood_at_time", 5)),
                        cause=e.get("cause", ""),
                        consequence=e.get("consequence", ""),
                        lesson=e.get("lesson", ""),
                        ts=occurred_at.isoformat(),
                    )
            except Exception as ex:
                logger.warning("Neo4j event failed: %s", ex)
        imported += 1
    logger.info("LifeEvents: imported %d / %d", imported, len(life_events))


async def import_core_psychology(session, user_id: int, psych: dict, mem0_client):
    """Store psychology profile as high-importance memories."""
    if not psych:
        return
    entries = []
    if psych.get("core_values"):
        entries.append(("core_values", f"Giá trị cốt lõi: {', '.join(psych['core_values'])}", 10))
    if psych.get("shadow_fears"):
        entries.append(("psychology", f"Nỗi sợ ngầm: {', '.join(psych['shadow_fears'])}", 10))
    if psych.get("avoidance_patterns"):
        entries.append(("psychology", f"Thói quen trốn tránh: {', '.join(psych['avoidance_patterns'])}", 9))
    if psych.get("dominant_emotion"):
        entries.append(("psychology", f"Cảm xúc chi phối: {psych['dominant_emotion']}", 8))
    if psych.get("archetype"):
        entries.append(("psychology", f"Archetype: {psych['archetype']}", 8))

    from db.models import Memory
    from sqlmodel import select
    for tags, content, importance in entries:
        stmt = select(Memory).where(Memory.user_id == user_id, Memory.content == content)
        if (await session.execute(stmt)).scalars().first():
            continue
        session.add(Memory(user_id=user_id, content=content, tags=tags, importance=importance))
        if mem0_client:
            try:
                mem0_client.add(
                    messages=[{"role": "user", "content": content}],
                    user_id=str(user_id),
                    metadata={"source": "core_psychology", "importance": importance},
                )
            except Exception as e:
                logger.warning("Mem0 psych failed: %s", e)
    await session.commit()
    logger.info("CorePsychology: imported %d entries", len(entries))


async def main(json_path: str, telegram_id: int):
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    logger.info("Loaded %s — user: %s", json_path, data.get("user_name", "?"))

    # Init DB
    from db.database import init_db, AsyncSessionLocal
    await init_db()

    # Init Mem0
    mem0_client = None
    try:
        from mem0 import Memory as Mem0Memory
        from config import settings
        mem0_cfg = {
            "version": "v1.1",
            "llm": {
                "provider": "openai",
                "config": {
                    "model": "deepseek-ai/deepseek-v4.1-flash",
                    "temperature": 0.0,
                    "api_key": settings.siliconflow_api_key,
                    "openai_base_url": "https://api.siliconflow.com/v1",
                    "max_tokens": 1500,
                }
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": "Qwen/Qwen3-Embedding-8B",
                    "api_key": settings.siliconflow_api_key,
                    "openai_base_url": "https://api.siliconflow.com/v1"
                },
            },
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "raphael_memories",
                    "path": "./data/chroma"
                },
            },
        }
        mem0_client = Mem0Memory.from_config(mem0_cfg)
        logger.info("Mem0 initialized")
    except Exception as e:
        logger.warning("Mem0 unavailable, skipping vector import: %s", e)

    # Init Neo4j
    driver = None
    try:
        from core.neo4j_client import get_neo4j_driver
        driver = get_neo4j_driver()
        if driver:
            logger.info("Neo4j connected")
    except Exception as e:
        logger.warning("Neo4j unavailable: %s", e)

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, telegram_id, data.get("user_name", "Master"))

        await import_memories(session, user.id, data.get("memories", []), mem0_client)
        await import_capabilities(session, user.id, data.get("capabilities", []))
        await import_physical_history(session, user.id, data.get("physical_history", []))
        await import_projects(session, user.id, data.get("projects", []))
        await import_life_states(session, user.id, data.get("life_states", []), driver)
        await import_life_events(session, user.id, data.get("life_events", []), mem0_client, driver)
        await import_core_psychology(session, user.id, data.get("core_psychology", {}), mem0_client)

    if driver:
        await driver.close()

    logger.info("=== Brain dump import complete ===")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/brain_dump_import.py <brain_dump.json> <telegram_id>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1], int(sys.argv[2])))
