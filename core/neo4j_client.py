import logging
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
