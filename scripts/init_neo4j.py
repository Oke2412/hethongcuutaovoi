import asyncio
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
