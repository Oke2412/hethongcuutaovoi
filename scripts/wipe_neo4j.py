import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.neo4j_client import get_neo4j_driver

async def wipe_neo4j():
    driver = get_neo4j_driver()
    if not driver:
        print('LỖI: Không thể kết nối Neo4j. Hãy đảm bảo Docker đang chạy.')
        return
        
    try:
        async with driver.session() as session:
            await session.run('MATCH (n) DETACH DELETE n')
        print('Đã wipe sạch sẽ Neo4j Graph Database để chuẩn bị cho Kiến trúc 3 Tầng!')
    except Exception as e:
        print(f'Lỗi khi wipe Neo4j: {e}')

if __name__ == '__main__':
    asyncio.run(wipe_neo4j())
