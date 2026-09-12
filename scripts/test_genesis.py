import asyncio
import os
import json
import glob
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from openai import AsyncOpenAI
from config import settings
client = AsyncOpenAI(api_key=settings.siliconflow_api_key, base_url='https://api.siliconflow.com/v1')
from core.ontology_prompt import ONTOLOGY_PROMPT_TEMPLATE
from core.neo4j_client import get_neo4j_driver

mock_queries = []
class MockSession:
    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc_val, exc_tb): pass
    async def run(self, query, **kwargs):
        global mock_queries
        mock_queries.append(f"CYPHER: {query} | PARAMS: {kwargs}")

class MockDriver:
    def session(self): return MockSession()

async def gather_massive_context():
    code_files = glob.glob('core/*.py') + glob.glob('bot/**/*.py', recursive=True) + glob.glob('docs/*.md') + glob.glob('*.md')
    context_code = "=== SOURCE CODE & BLUEPRINT ===\n"
    for filepath in code_files:
        if os.path.isfile(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    context_code += f"--- FILE: {filepath} ---\n{f.read()}\n"
            except: pass
            
    brain_dir = 'C:/Users/Asus/.gemini/antigravity/brain'
    log_files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))
    
    sessions_data = []
    for idx, log_path in enumerate(log_files):
        session_text = f"\n=== SESSION ID: {idx+1} ===\n"
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if data.get('type') in ['USER_INPUT', 'PLANNER_RESPONSE'] and data.get('content'):
                            session_text += f"[{data.get('source')}]: {data.get('content')}\n"
                    except: pass
            sessions_data.append({"id": idx+1, "text": session_text})
        except: pass
        
    all_sessions_text = "".join([s['text'] for s in sessions_data])
    massive_context = context_code + "\n=== HE THONG LICH SU CHAT ===\n" + all_sessions_text
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
        return "SUCCESS"
    except Exception as e:
        return f"ERROR: {e}"

async def main():
    log_output = []
    log_output.append("--- MOCK TEST GENESIS INGESTION --- ")
    
    print("Dang load du lieu...")
    massive_context, sessions_data = await gather_massive_context()
    log_output.append(f"Da load {len(sessions_data)} sessions. Khoi luong context: {len(massive_context)} chars.")
    
    driver = get_neo4j_driver()
    if not driver:
        log_output.append("WARNING: Khong the ket noi Neo4j server.")
        return
    else:
        log_output.append("Neo4j Connected: Hop le.")
        async with driver.session() as s:
            await s.run("MERGE (u:User {telegram_id: 0, name: 'The Master'})")
    
    test_batch = sessions_data[:2]
    batch_ids = [s['id'] for s in test_batch]
    log_output.append(f"Dang goi API cho test batch: {batch_ids}...")
    
    prompt = f"""{ONTOLOGY_PROMPT_TEMPLATE}

[NGU CANH TOAN CUOC BAT DAU DUOI DAY]
{massive_context}
[NGU CANH TOAN CUOC KET THUC]

NHIEM VU: 
Trich xuat Do thi 3 Tang NHUNG CHI DANH CHO CAC SESSION ID: {batch_ids}.
"""
    try:
        api_resp = await client.chat.completions.create(model="deepseek-ai/deepseek-v4.1-flash", messages=[{"role": "user", "content": prompt}], temperature=0.0)
        response = api_resp.choices[0].message.content
        log_output.append("\n[RAW API RESPONSE]:\n" + response)
        
        json_match = re.search(r'\{.*\}', response.replace('\n', ''), re.DOTALL)
        if json_match:
            parsed_data = json.loads(json_match.group(0))
            graph_data = parsed_data.get("neo4j", parsed_data)
            log_output.append("\n[JSON PARSE SUCCESS]!")
            db_status = await inject_to_neo4j(driver, graph_data)
            log_output.append(f"Ket qua nap DB: {db_status}")
            if mock_queries:
                log_output.append("\n[MOCK CYPHER QUERIES GENERATED]:")
                for mq in mock_queries: log_output.append(mq)
        else:
            log_output.append("\n[JSON PARSE FAILED] Khong tim thay JSON hop le.")
    except Exception as e:
        log_output.append(f"\n[API ERROR]: {e}")
        
    with open('mock_ingest.log', 'w', encoding='utf-8') as f:
        f.write("\n".join(log_output))
    print("Test hoan tat. Hay xem file mock_ingest.log")

if __name__ == '__main__':
    asyncio.run(main())