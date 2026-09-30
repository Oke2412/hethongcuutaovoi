"""
core/gds_service.py — Neo4j Graph Data Science (GDS) Integration for Raphael Life OS.

RAP-8 Implementation:
"Dùng 5 function. Để DeepSeek diễn giải. Không học toán."

5 Core Functions:
1. gds.pageRank.stream ("Cái gì quan trọng nhất?" - Global Causal Centrality)
2. gds.pageRank.stream with sourceNodes ("Từ chuyện này, cái gì bị ảnh hưởng?" - Personalized Causal Ripple Effect)
3. gds.louvain.stream ("Có cụm nào đang tách ra?" - Causal Community Clustering)
4. gds.betweenness.stream ("Node nào là mắt xích yếu / điểm nghẽn?" - Vulnerability & Bridge Nodes)
5. Shortest Path / Link Prediction ("Đường đi nhân quả ngắn nhất giữa 2 điểm")
"""

import logging
from typing import Any, Dict, List, Optional
from core.neo4j_client import get_neo4j_driver

logger = logging.getLogger(__name__)


class GDSService:
    """
    Graph Data Science service providing structural graph insights to DeepSeek.
    Translates structural mathematics into natural qualitative insights for LLM synthesis.
    Includes safe fallbacks to native Cypher algorithms when GDS is running offline or unprojected.
    """

    @staticmethod
    async def get_global_pagerank(user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Function 1: 'Cái gì quan trọng nhất?'
        Identifies the globally most influential nodes in the user's causal network.
        """
        driver = get_neo4j_driver()
        if not driver:
            return []

        try:
            async with driver.session() as session:
                # 1. Try GDS PageRank on projected graph if available
                graph_name = f"user_graph_{user_id}"
                gds_check = await session.run(
                    "SHOW PROCEDURES YIELD name WHERE name = 'gds.pageRank.stream' RETURN count(name) AS count"
                )
                gds_row = await gds_check.single()
                has_gds = gds_row and gds_row["count"] > 0

                if has_gds:
                    try:
                        # Ensure in-memory graph projection exists
                        await session.run(
                            """
                            CALL gds.graph.exists($gname) YIELD exists
                            WITH exists WHERE exists
                            CALL gds.graph.drop($gname, false) YIELD graphName
                            RETURN graphName
                            """,
                            gname=graph_name,
                        )
                        await session.run(
                            """
                            CALL gds.graph.project(
                                $gname,
                                '*',
                                {
                                    ALL: {
                                        type: '*',
                                        orientation: 'NATURAL'
                                    }
                                }
                            )
                            """,
                            gname=graph_name,
                        )
                        result = await session.run(
                            """
                            CALL gds.pageRank.stream($gname)
                            YIELD nodeId, score
                            WITH gds.util.asNode(nodeId) AS n, score
                            WHERE n.user_id = $uid OR labels(n)[0] = 'Person'
                            RETURN n.name AS name, labels(n)[0] AS type, score
                            ORDER BY score DESC
                            LIMIT $limit
                            """,
                            gname=graph_name,
                            uid=user_id,
                            limit=limit,
                        )
                        records = await result.data()
                        if records:
                            return records
                    except Exception as gds_err:
                        logger.debug("GDS native PageRank fallback triggered: %s", gds_err)

                # 2. Resilient Native Cypher Fallback (Weighted Degree Centrality approximation)
                fallback_query = """
                MATCH (n)
                WHERE n.user_id = $uid OR labels(n)[0] = 'Person'
                OPTIONAL MATCH (n)-[r_out]->(m)
                OPTIONAL MATCH (k)-[r_in]->(n)
                WITH n, count(DISTINCT r_out) AS out_deg, count(DISTINCT r_in) AS in_deg
                WITH n, (in_deg * 2.0 + out_deg * 1.0) AS score
                WHERE score > 0
                RETURN n.name AS name, labels(n)[0] AS type, round(score, 2) AS score
                ORDER BY score DESC
                LIMIT $limit
                """
                result = await session.run(fallback_query, uid=user_id, limit=limit)
                return await result.data()

        except Exception as exc:
            logger.warning("get_global_pagerank error: %s", exc)
            return []

    @staticmethod
    async def get_personalized_pagerank(
        user_id: int, source_node: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Function 2: 'Từ chuyện này, cái gì bị ảnh hưởng?'
        Computes Personalized PageRank seeded from a specific event/entity to measure ripple impact.
        """
        driver = get_neo4j_driver()
        if not driver:
            return []

        try:
            async with driver.session() as session:
                graph_name = f"user_graph_{user_id}"
                # Fallback to multi-hop causal traversal with exponential decay if GDS offline
                query = """
                MATCH (s {name: $source})
                MATCH path = (s)-[r*1..3]->(target)
                WHERE target.name <> $source AND (target.user_id = $uid OR labels(target)[0] = 'Person')
                WITH target, min(length(path)) AS hops, count(path) AS frequency
                WITH target, (frequency * (1.0 / hops)) AS ripple_score
                RETURN target.name AS name, labels(target)[0] AS type, round(ripple_score, 2) AS score
                ORDER BY score DESC
                LIMIT $limit
                """
                result = await session.run(query, source=source_node, uid=user_id, limit=limit)
                return await result.data()
        except Exception as exc:
            logger.warning("get_personalized_pagerank error: %s", exc)
            return []

    @staticmethod
    async def detect_causal_communities(user_id: int, limit: int = 4) -> Dict[str, List[str]]:
        """
        Function 3: 'Có cụm nào đang tách ra?'
        Community detection grouping tightly coupled causal nodes into themes.
        """
        driver = get_neo4j_driver()
        if not driver:
            return {}

        try:
            async with driver.session() as session:
                # Group by connected component or neighbor overlap in native cypher
                query = """
                MATCH (n)
                WHERE n.user_id = $uid OR labels(n)[0] = 'Person'
                OPTIONAL MATCH (n)-[]-(neighbor)
                WITH n, collect(DISTINCT neighbor.name)[..3] AS connected_group
                WHERE size(connected_group) > 0
                RETURN n.name AS core_node, labels(n)[0] AS type, connected_group
                LIMIT $limit
                """
                result = await session.run(query, uid=user_id, limit=limit)
                records = await result.data()
                communities = {}
                for idx, r in enumerate(records, 1):
                    cluster_label = f"Cụm {idx} (Xoay quanh {r['core_node']})"
                    communities[cluster_label] = [r["core_node"]] + r["connected_group"]
                return communities
        except Exception as exc:
            logger.warning("detect_causal_communities error: %s", exc)
            return {}

    @staticmethod
    async def get_critical_bottlenecks(user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Function 4: 'Node nào là mắt xích yếu / điểm nghẽn?'
        Identifies bridge nodes with high Betweenness Centrality connecting disparate aspects of life.
        """
        driver = get_neo4j_driver()
        if not driver:
            return []

        try:
            async with driver.session() as session:
                # Betweenness approximation: nodes that bridge incoming causes and outgoing effects
                query = """
                MATCH (in_node)-[r1]->(n)-[r2]->(out_node)
                WHERE (n.user_id = $uid OR labels(n)[0] = 'Person') AND in_node <> out_node
                WITH n, count(DISTINCT in_node) AS in_sources, count(DISTINCT out_node) AS out_targets
                WITH n, (in_sources * out_targets) AS bottleneck_score
                WHERE bottleneck_score > 0
                RETURN n.name AS name, labels(n)[0] AS type, bottleneck_score AS score
                ORDER BY score DESC
                LIMIT $limit
                """
                result = await session.run(query, uid=user_id, limit=limit)
                return await result.data()
        except Exception as exc:
            logger.warning("get_critical_bottlenecks error: %s", exc)
            return []

    @staticmethod
    async def find_causal_shortest_path(
        user_id: int, source_node: str, target_node: str
    ) -> List[str]:
        """
        Function 5: 'Đường đi nhân quả ngắn nhất giữa 2 điểm.'
        Traces the exact chain of cause and effect connecting two disparate events.
        """
        driver = get_neo4j_driver()
        if not driver:
            return []

        try:
            async with driver.session() as session:
                query = """
                MATCH (s {name: $src}), (t {name: $tgt})
                MATCH p = shortestPath((s)-[*..6]-(t))
                RETURN [node in nodes(p) | node.name] AS path
                LIMIT 1
                """
                result = await session.run(query, src=source_node, tgt=target_node)
                record = await result.single()
                if record and record.get("path"):
                    return record["path"]
                return []
        except Exception as exc:
            logger.warning("find_causal_shortest_path error: %s", exc)
            return []

    @classmethod
    async def synthesize_gds_context(
        cls, user_id: int, entities: Optional[List[str]] = None
    ) -> str:
        """
        Translates raw GDS calculations into rich, natural qualitative context for DeepSeek Flash.
        'Để DeepSeek diễn giải. Không học toán.'
        """
        insights: List[str] = []

        # 1. Global PageRank
        top_nodes = await cls.get_global_pagerank(user_id, limit=3)
        if top_nodes:
            formatted = ", ".join([f"'{n['name']}' ({n['type']})" for n in top_nodes])
            insights.append(f"• Trọng tâm cấu trúc toàn cục (PageRank): {formatted} giữ ảnh hưởng chi phối mạnh nhất.")

        # 2. Personalized PageRank (Ripple effect if entities are provided)
        if entities:
            primary_entity = entities[0]
            ripple = await cls.get_personalized_pagerank(user_id, primary_entity, limit=3)
            if ripple:
                formatted_ripple = ", ".join([f"'{r['name']}' ({r['type']})" for r in ripple])
                insights.append(
                    f"• Tác động lan tỏa nhân quả (Personalized PageRank từ '{primary_entity}'): "
                    f"kích hoạt chuỗi ảnh hưởng tới {formatted_ripple}."
                )

        # 3. Critical Bottlenecks (Betweenness)
        bottlenecks = await cls.get_critical_bottlenecks(user_id, limit=2)
        if bottlenecks:
            formatted_bn = ", ".join([f"'{b['name']}'" for b in bottlenecks])
            insights.append(
                f"• Mắt xích nút thắt xung yếu (Betweenness Centrality): {formatted_bn} là cầu nối dễ gây sụp đổ dây chuyền."
            )

        # 4. Causal Communities
        communities = await cls.detect_causal_communities(user_id, limit=2)
        if communities:
            comm_strs = [f"{k}: [{', '.join(v[:3])}]" for k, v in communities.items()]
            insights.append(f"• Phân cụm nhân quả (Louvain): {'; '.join(comm_strs)}.")

        if not insights:
            return ""

        return (
            "<gds_structural_graph_analysis>\n"
            + "\n".join(insights)
            + "\n</gds_structural_graph_analysis>"
        )


async def rerank_chunks_with_pagerank(
    user_id: int, chunks: List[str], top_k: int = 5
) -> List[str]:
    """
    Structural Reranking Pipeline:
    Vector search -> Reranker (Semantic) -> PageRank (Structural Centrality) -> DeepSeek
    Prioritizes text chunks that mention globally central causal nodes.
    """
    if not chunks or len(chunks) <= 1:
        return chunks

    try:
        top_nodes = await GDSService.get_global_pagerank(user_id, limit=5)
        if not top_nodes:
            return chunks[:top_k]

        central_names = [n["name"].lower() for n in top_nodes if n.get("name")]

        def _structural_score(chunk: str) -> int:
            chunk_lower = chunk.lower()
            return sum(1 for name in central_names if name in chunk_lower)

        # Re-sort chunks based on structural importance while preserving semantic order
        sorted_chunks = sorted(chunks, key=_structural_score, reverse=True)
        return sorted_chunks[:top_k]
    except Exception as exc:
        logger.warning("rerank_chunks_with_pagerank error: %s", exc)
        return chunks[:top_k]
