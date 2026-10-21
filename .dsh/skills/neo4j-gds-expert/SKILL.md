---
name: neo4j-gds-expert
description: >-
  Expert guidelines, Cypher best practices, and runbooks for Neo4j Graph Data Science (GDS),
  in-memory graph projections, APOC procedures, and 3-tier causal GraphRAG architectures.
  Use this skill whenever querying Neo4j, designing graph schemas, executing GDS algorithms
  (PageRank, Louvain, Betweenness, Shortest Path), or diagnosing Neo4j connection issues.
---

# Neo4j Graph Data Science & Causal GraphRAG Expert

This skill provides step-by-step procedures for administering, querying, and running Graph Data Science (GDS) algorithms on Neo4j within the Raphael Life OS ecosystem.

## Core Rules & Invariants

1. **Always Use `MERGE` Instead of `CREATE`**:
   Never use raw `CREATE` for domain entities. Always use `MERGE (n:Label {name: $name})` with `ON CREATE SET` or `SET` to avoid duplicate node garbage.

2. **3-Layer Causal Schema**:
   - **Physical Layer**: `Person`, `Location`, `Object`, `LifeEvent`
   - **Cognitive Layer**: `Emotion`, `DefenseMechanism`, `CoreBelief`
   - **Edges**: `TRIGGERS`, `CAUSES`, `REINFORCES`, `MITIGATES`, `LOCATED_IN`, `RELATED_TO`, `VISITED`, `EXPERIENCED`

3. **In-Memory Graph Projection (`gds.graph.project`)**:
   Always project graphs as **`UNDIRECTED`** if running Louvain or Betweenness, because directed graphs often isolate components and produce zero modularity.
   Always verify if a projection already exists before projecting to avoid projection collision errors.

---

## 5 Core GDS Functions Reference

| Function | Natural Question | Cypher Call | Use Case |
|---|---|---|---|
| **1. PageRank** | *What is most important?* | `gds.pageRank.stream` | Identifies root causal nodes and core life priorities |
| **2. Personalized PageRank** | *What is affected by this event?* | `gds.pageRank.stream` + `sourceNodes` | Causal ripple effect from a specific trigger node |
| **3. Louvain Community** | *What clusters are separating?* | `gds.louvain.stream` | Psychological compartmentalization (e.g. Work vs Escapism) |
| **4. Betweenness Centrality** | *Where is the critical bottleneck?* | `gds.betweenness.stream` | Systemic vulnerability bridge nodes connecting disparate clusters |
| **5. Shortest Path** | *What connects A to B?* | `gds.shortestPath.dijkstra.stream` | Exact chain of causation between two events or beliefs |

Detailed algorithm examples and Cypher templates are in [references/gds-algorithms.md](./references/gds-algorithms.md).

---

## Quick Diagnostic & Healthcheck

Run the bundled diagnostic script to verify Bolt connectivity, APOC/GDS plugin installation, and in-memory projection health:

```bash
python scripts/verify_projection.py --uri bolt://localhost:7687 --user neo4j --password password
```

## Step-by-Step GDS Workflow

1. **Verify Plugins**:
   ```cypher
   CALL gds.version() YIELD version;
   SHOW PROCEDURES YIELD name WHERE name STARTS WITH 'apoc.' RETURN count(name);
   ```

2. **Project In-Memory Graph**:
   ```cypher
   CALL gds.graph.project(
       'user_graph_proj',
       '*',
       { ALL: { type: '*', orientation: 'UNDIRECTED' } }
   );
   ```

3. **Stream Algorithm Results**:
   ```cypher
   CALL gds.pageRank.stream('user_graph_proj')
   YIELD nodeId, score
   WITH gds.util.asNode(nodeId) AS n, score
   WHERE n.name IS NOT NULL
   RETURN n.name AS name, labels(n)[0] AS type, round(score, 3) AS score
   ORDER BY score DESC LIMIT 5;
   ```

4. **Drop Projection When Done (or on Refresh)**:
   ```cypher
   CALL gds.graph.drop('user_graph_proj', false);
   ```
