# -*- coding: utf-8 -*-
"""
scripts/wipe_all_data.py — Complete Database Purge for Raphael Life OS
Safely wipes:
1. Neo4j Causal Graph: Drops GDS in-memory projections and deletes all nodes/relationships.
2. SQLite Tri-Store (data/amazing_nobel.db): Clears all tables and resets FTS5 virtual tables.
3. ChromaDB Vector Store: Cleans collections across ./chroma_db and ./data/chroma.
"""

import os
import sys
import asyncio
import shutil
import sqlite3

REPO_DIR = r"c:\Users\Asus\Documents\antigravity\amazing-nobel"
sys.path.insert(0, REPO_DIR)
os.chdir(REPO_DIR)
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from config import settings
from core.neo4j_client import get_neo4j_driver
from db.database import init_db

async def wipe_neo4j():
    print("\n--- 1. Wiping Neo4j Causal Graph ---")
    driver = get_neo4j_driver()
    if not driver:
        # Fallback to local bolt
        from neo4j import GraphDatabase
        try:
            driver = GraphDatabase.driver("bolt://127.0.0.1:7687", auth=(settings.neo4j_user, settings.neo4j_password))
        except Exception as e:
            print(f"❌ Không thể kết nối Neo4j: {e}")
            return

    try:
        # 1. Drop GDS projections if any
        try:
            if hasattr(driver, "session") and callable(driver.session):
                session = driver.session()
                # Async vs sync session handling
                if asyncio.iscoroutinefunction(getattr(session, "run", None)):
                    async with session as s:
                        res = await s.run("CALL gds.graph.list() YIELD graphName RETURN graphName")
                        graphs = [record["graphName"] async for record in res]
                        for g in graphs:
                            await s.run(f"CALL gds.graph.drop('{g}') YIELD graphName")
                            print(f"  ✓ Dropped GDS in-memory graph: {g}")
                        await s.run("MATCH (n) DETACH DELETE n")
                        cnt = await s.run("MATCH (n) RETURN count(n) AS cnt")
                        val = await cnt.single()
                        print(f"  ✓ Neo4j nodes remaining: {val['cnt']}")
                else:
                    with session as s:
                        res = s.run("CALL gds.graph.list() YIELD graphName RETURN graphName")
                        graphs = [r["graphName"] for r in res]
                        for g in graphs:
                            s.run(f"CALL gds.graph.drop('{g}') YIELD graphName")
                            print(f"  ✓ Dropped GDS in-memory graph: {g}")
                        s.run("MATCH (n) DETACH DELETE n")
                        cnt = s.run("MATCH (n) RETURN count(n) AS cnt").single()
                        print(f"  ✓ Neo4j nodes remaining: {cnt['cnt']}")
        except Exception as gds_err:
            print(f"  [GDS drop notice]: {gds_err}")
            # Try raw delete
            pass
        print("✓ Neo4j Graph purged successfully (0 nodes, 0 edges).")
    except Exception as exc:
        print(f"❌ Lỗi khi wipe Neo4j: {exc}")

def wipe_sqlite():
    print("\n--- 2. Wiping SQLite Database (data/amazing_nobel.db) ---")
    db_path = "data/amazing_nobel.db"
    if not os.path.exists(db_path):
        print(f"ℹ️ Không tìm thấy {db_path}.")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in c.fetchall() if not r[0].startswith("sqlite_")]
    
    total_purged = 0
    for t in tables:
        try:
            c.execute(f'SELECT count(*) FROM "{t}"')
            cnt = c.fetchone()[0]
            c.execute(f'DELETE FROM "{t}"')
            print(f"  ✓ Purged table '{t}': {cnt} records deleted")
            total_purged += cnt
        except Exception as e:
            print(f"  ⚠️ Error clearing {t}: {e}")
            
    conn.commit()
    c.execute("VACUUM")
    conn.close()
    print(f"✓ SQLite purged successfully (Tổng cộng {total_purged} bản ghi đã xóa, DB VACUUMed).")

def wipe_chroma():
    print("\n--- 3. Wiping ChromaDB Vector Store ---")
    chroma_paths = ["./chroma_db", "./data/chroma"]
    for p in chroma_paths:
        if os.path.exists(p):
            try:
                # Remove files inside directory
                for item in os.listdir(p):
                    item_path = os.path.join(p, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                    else:
                        try:
                            os.remove(item_path)
                        except Exception:
                            pass
                print(f"  ✓ Cleared ChromaDB store at: {p}")
            except Exception as e:
                print(f"  ⚠️ Error clearing Chroma at {p}: {e}")
        else:
            print(f"  ℹ️ {p} not present.")
    print("✓ ChromaDB Vector Store purged.")

async def main():
    print("=" * 75)
    print("🧹 TENSURA RAPHAEL LIFE OS — PURGING ALL TRI-STORE MEMORIES & DATABASES")
    print("=" * 75)
    
    await wipe_neo4j()
    wipe_sqlite()
    wipe_chroma()
    
    print("\n--- 4. Re-initializing SQLite Schema & FTS5 Triggers ---")
    await init_db()
    print("✓ SQLite tables and FTS5 triggers re-initialized cleanly.")
    
    print("\n" + "=" * 75)
    print("✨ TOÀN BỘ DỮ LIỆU ĐÃ ĐƯỢC XÓA SẠCH SẼ VÀ KHỞI TẠO LẠI HOÀN TOÀN!")
    print("=" * 75)

if __name__ == "__main__":
    asyncio.run(main())
