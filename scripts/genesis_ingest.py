import asyncio
import os
import json
import glob
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.llm import get_ai_response
from core.ontology_prompt import ONTOLOGY_PROMPT_TEMPLATE
from core.neo4j_client import get_neo4j_driver

async def gather_massive_context():
    code_files = glob.glob('core/*.py') + glob.glob('bot/**/*.py', recursive=True) + glob.glob('docs/*.md') + glob.glob('*.md')
    context_code = "=== SOURCE CODE & BLUEPRINT ===\n"
    for filepath in code_files:
        if os.path.isfile(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    context_code += f"--- FILE: {filepath} ---\n{f.read()}\n"
            except: pass
            
    log_files = ['docs/tien_kiep/MASTER_TIEN_KIEP.md', 'PROMPT_HISTORY.md']
    sessions_data = []
    for idx, log_path in enumerate(log_files):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                sessions_data.append({'id': idx+1, 'text': f.read()})
        except: pass
    all_sessions_text = "".join([s['text'] for s in sessions_data])
    massive_context = context_code + "\n=== HỆ THỐNG LỊCH SỬ CHAT ===\n" + all_sessions_text
    return massive_context, sessions_data

async def inject_to_neo4j(driver, json_data):
    try:
        async with driver.session() as session:
            for node in json_data.get("nodes", []):
                label, name = node.get("label"), node.get("name")
                if label and name:
                    await session.run(f"MERGE (n:{label} {{name: $name}}) SET n.timestamp = $ts, n.h3_index = $h3", name=name, ts=node.get("timestamp"), h3=node.get("h3_index"))
                    await session.run(f"MATCH (u:User), (n:{label} {{name: $name}}) MERGE (u)-[:EXPERIENCED]->(n)", name=name)
                    
            for edge in json_data.get("edges", []):
                src_id, tgt_id, rel = edge.get("source"), edge.get("target"), edge.get("type")
                src_node = next((n for n in json_data.get("nodes", []) if n.get("id") == src_id), None)
                tgt_node = next((n for n in json_data.get("nodes", []) if n.get("id") == tgt_id), None)
                if src_node and tgt_node:
                    query = f"MATCH (a:{src_node['label']} {{name: $src_name}}), (b:{tgt_node['label']} {{name: $tgt_name}}) MERGE (a)-[:{rel}]->(b)"
                    await session.run(query, src_name=src_node['name'], tgt_name=tgt_node['name'])
    except Exception as e:
        print(f"  [!] Lỗi ghi DB: {e}")

async def main():
    print("1. Đang gom dữ liệu (726k+ tokens)...")
    massive_context, sessions_data = await gather_massive_context()
    
    driver = get_neo4j_driver()
    if not driver:
        print("LỖI: Không kết nối được Neo4j. Đảm bảo server/docker đang chạy.")
        return
        
    batch_size = 5
    print(f"2. Bắt đầu nạp liệu cho {len(sessions_data)} sessions. Sẽ chia thành các batch {batch_size} sessions.")
    
    async with driver.session() as s:
        await s.run("MERGE (u:User {telegram_id: 0, name: 'The Master'})")
        
    for i in range(0, len(sessions_data), batch_size):
        batch = sessions_data[i:i+batch_size]
        batch_ids = [s['id'] for s in batch]
        print(f"\n>>> Đang xử lý Batch {i//batch_size + 1} (Sessions: {batch_ids})...")
        
        prompt = f"""{ONTOLOGY_PROMPT_TEMPLATE}

[NGỮ CẢNH TOÀN CỤC BẮT ĐẦU DƯỚI ĐÂY]
{massive_context}
[NGỮ CẢNH TOÀN CỤC KẾT THÚC]

NHIỆM VỤ: 
Trích xuất Đồ thị 3 Tầng NHƯNG CHỈ DÀNH CHO CÁC SESSION ID: {batch_ids}.
"""
        try:
            response = await get_ai_response(prompt, model="deepseek-ai/deepseek-v4.1-flash", temperature=0.0)
            
            json_match = re.search(r'\{.*\}', response.replace('\n', ''), re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group(0))
                graph_data = parsed_data.get("neo4j", parsed_data)
                print(f"  [+] Trix xuat thanh cong: {len(graph_data.get("nodes", []))} nodes, {len(graph_data.get("edges", []))} edges.")
                await inject_to_neo4j(driver, graph_data)
            else:
                print("  [!] LLM không trả về JSON hợp lệ.")
                
        except Exception as e:
            print(f"  [!] Lỗi API: {e}")
            
        await asyncio.sleep(30)
        
    print("\n HOÀN THÀNH GENESIS INGESTION!")

if __name__ == '__main__':
    asyncio.run(main())
