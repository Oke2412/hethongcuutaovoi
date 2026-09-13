import asyncio
import sys
import json
import os
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from openai import AsyncOpenAI
from config import settings
from core.neo4j_client import get_neo4j_driver
from core.ontology_prompt import ONTOLOGY_PROMPT_TEMPLATE

client = AsyncOpenAI(api_key=settings.siliconflow_api_key, base_url='https://api.siliconflow.com/v1')

async def extract_graph(text):
    prompt = ONTOLOGY_PROMPT_TEMPLATE.replace("{TEXT_CONTENT}", text)
    resp = await client.chat.completions.create(
        model="deepseek-ai/deepseek-v4.1-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    res = resp.choices[0].message.content
    match = re.search(r'```json\n(.*?)\n```', res, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    return json.loads(res)

async def inject_to_neo4j(json_data):
    driver = get_neo4j_driver()
    if not driver:
        print("No Neo4j driver.")
        return
    
    try:
        async with driver.session() as session:
            # Nodes
            for node in json_data.get("nodes", []):
                label, name = node.get("label"), node.get("name")
                if label and name:
                    props = {k: v for k, v in node.items() if k not in ["label", "name"]}
                    prop_str = ", ".join([f"n.{k} = ${k}" for k in props.keys()])
                    query = f"MERGE (n:{label} {{name: $name}})"
                    if prop_str:
                        query += f" SET {prop_str}"
                    await session.run(query, name=name, **props)
            
            # Relationships
            for edge in json_data.get("relationships", []):
                s_label = edge.get("source_label")
                s_name = edge.get("source_name")
                t_label = edge.get("target_label")
                t_name = edge.get("target_name")
                rel_type = edge.get("type")
                if all([s_label, s_name, t_label, t_name, rel_type]):
                    props = {k: v for k, v in edge.items() if k not in ["source_label", "source_name", "target_label", "target_name", "type"]}
                    prop_str = ", ".join([f"r.{k} = ${k}" for k in props.keys()])
                    query = f"""
                    MATCH (s:{s_label} {{name: $s_name}})
                    MATCH (t:{t_label} {{name: $t_name}})
                    MERGE (s)-[r:{rel_type}]->(t)
                    """
                    if prop_str:
                        query += f" SET {prop_str}"
                    await session.run(query, s_name=s_name, t_name=t_name, **props)
        print("Ingested successfully!")
    except Exception as e:
        print(f"Failed to ingest: {e}")
    finally:
        await driver.close()

async def main():
    if len(sys.argv) < 2:
        return
    filepath = sys.argv[1]
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print("Extracting graph JSON via LLM...")
    json_data = await extract_graph(text)
    print("\n--- RAW JSON EXTRACTED FROM LLM ---")
    print(json.dumps(json_data, indent=2, ensure_ascii=False))
    print("-----------------------------------\n")
    print("Injecting into Neo4j...")
    await inject_to_neo4j(json_data)

if __name__ == "__main__":
    asyncio.run(main())
