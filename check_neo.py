
from neo4j import GraphDatabase
from config import settings
import json

driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
with driver.session() as session:
    res = session.run('MATCH (n) RETURN labels(n) AS labels, properties(n) AS props LIMIT 30')
    records = []
    for r in res:
        records.append({'labels': r['labels'], 'props': r['props']})
    with open('neo4j_dump.json', 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

