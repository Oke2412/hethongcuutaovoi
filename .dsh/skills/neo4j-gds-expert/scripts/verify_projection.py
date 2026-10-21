import asyncio
import sys
from neo4j import AsyncGraphDatabase

async def verify_gds(uri="bolt://localhost:7687", user="neo4j", password="password"):
    print(f"Connecting to Neo4j Bolt at {uri}...")
    try:
        driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        async with driver.session() as session:
            # 1. Neo4j Component check
            res = await session.run("CALL dbms.components() YIELD name, versions RETURN name, versions")
            row = await res.single()
            print(f"[OK] Neo4j Engine: {row['name']} {row['versions']}")

            # 2. GDS Plugin check
            gds_res = await session.run("CALL gds.version() YIELD version RETURN version")
            gds_row = await gds_res.single()
            print(f"[OK] GDS Plugin Active: v{gds_row['version']}")

            # 3. Node count
            cnt_res = await session.run("MATCH (n) RETURN count(n) AS cnt")
            cnt_row = await cnt_res.single()
            print(f"[OK] Total Knowledge Graph Nodes: {cnt_row['cnt']}")

        await driver.close()
        print("[SUCCESS] Neo4j GDS environment is operational.")
    except Exception as exc:
        print(f"[ERROR] Verification failed: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(verify_gds())
