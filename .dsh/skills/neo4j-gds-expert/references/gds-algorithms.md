# Neo4j GDS Algorithm Reference Templates

## 1. Global PageRank
Finds globally influential nodes (root causes, central figures).
```cypher
CALL gds.pageRank.stream($graph_name)
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS n, score
WHERE n.name IS NOT NULL
RETURN n.name AS name, labels(n)[0] AS type, round(score, 3) AS score
ORDER BY score DESC LIMIT 5;
```

## 2. Personalized PageRank (Ripple Effect)
Computes ripple impact propagating outward from a specific source entity.
```cypher
MATCH (source {name: $source_name})
CALL gds.pageRank.stream($graph_name, {
    sourceNodes: [source],
    dampingFactor: 0.85
})
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS n, score
WHERE n.name IS NOT NULL AND n.name <> $source_name
RETURN n.name AS name, labels(n)[0] AS type, round(score, 3) AS score
ORDER BY score DESC LIMIT 5;
```

## 3. Louvain Community Detection
Detects isolated or tightly bound psychological/social communities.
```cypher
CALL gds.louvain.stream($graph_name)
YIELD nodeId, communityId
WITH gds.util.asNode(nodeId) AS n, communityId
WHERE n.name IS NOT NULL
RETURN communityId, collect(n.name)[..5] AS members, count(n) AS size
ORDER BY size DESC LIMIT 4;
```

## 4. Betweenness Centrality (Bottlenecks)
Identifies bridge nodes that control information or causal flow between communities.
```cypher
CALL gds.betweenness.stream($graph_name)
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS n, score
WHERE n.name IS NOT NULL
RETURN n.name AS name, labels(n)[0] AS type, round(score, 3) AS score
ORDER BY score DESC LIMIT 5;
```

## 5. Shortest Path (Causal Chain)
Extracts the exact causal path between an event and an emotional or behavioral outcome.
```cypher
MATCH (source {name: $src_name}), (target {name: $tgt_name})
CALL gds.shortestPath.dijkstra.stream($graph_name, {
    sourceNode: source,
    targetNode: target
})
YIELD index, sourceNode, targetNode, totalCost, nodeIds
RETURN [nodeId IN nodeIds | gds.util.asNode(nodeId).name] AS causal_chain, totalCost;
```
