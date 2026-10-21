"""
tests/test_gds_service.py — Unit and integration tests for Neo4j Graph Data Science (GDS).
Validates the 5 GDS functions, qualitative synthesis, structural reranking, and offline fallback.
"""

import os
import sys
import unittest
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.abspath("."))
from core.gds_service import GDSService, rerank_chunks_with_pagerank


class TestGDSService(unittest.IsolatedAsyncioTestCase):

    async def test_offline_fallback_safety(self):
        """When Neo4j driver is None or offline, GDS functions must return safe defaults without throwing."""
        with patch("core.gds_service.get_neo4j_driver", return_value=None):
            # Function 1: PageRank
            pagerank = await GDSService.get_global_pagerank(user_id=123)
            self.assertEqual(pagerank, [])

            # Function 2: Personalized PageRank
            ripple = await GDSService.get_personalized_pagerank(user_id=123, source_node="Board mạch")
            self.assertEqual(ripple, [])

            # Function 3: Communities (Louvain)
            communities = await GDSService.detect_causal_communities(user_id=123)
            self.assertEqual(communities, {})

            # Function 4: Bottlenecks (Betweenness)
            bottlenecks = await GDSService.get_critical_bottlenecks(user_id=123)
            self.assertEqual(bottlenecks, [])

            # Function 5: Shortest Path
            path = await GDSService.find_causal_shortest_path(user_id=123, source_node="A", target_node="B")
            self.assertEqual(path, [])

            # Synthesis for LLM
            synthesis = await GDSService.synthesize_gds_context(user_id=123, entities=["A", "B"])
            self.assertEqual(synthesis, "")

    async def test_rerank_chunks_with_pagerank_structural_ordering(self):
        """Chunks mentioning high-PageRank central nodes should be prioritized to the top."""
        mock_top_nodes = [
            {"name": "Board mạch STM32", "type": "Object", "score": 4.5},
            {"name": "TS. Hùng", "type": "Person", "score": 3.8},
        ]
        with patch.object(GDSService, "get_global_pagerank", AsyncMock(return_value=mock_top_nodes)):
            chunks = [
                "Master đang uống cafe và cảm thấy hơi mệt mỏi.",
                "Thầy TS. Hùng yêu cầu hoàn thành định vị SLAM ngoài thực địa.",
                "Cái Board mạch STM32 đã bị nổ do chập điện 24V.",
                "Thời tiết hôm nay có gió nhẹ và mây rải rác.",
            ]
            reranked = await rerank_chunks_with_pagerank(user_id=123, chunks=chunks, top_k=3)
            self.assertEqual(len(reranked), 3)
            # The top chunks must contain the central nodes
            self.assertTrue(any("Board mạch STM32" in c or "TS. Hùng" in c for c in reranked[:2]))

    async def test_synthesize_gds_context_formatting(self):
        """Validates that GDS insights are translated into clean qualitative tags for DeepSeek Flash."""
        with patch.object(
            GDSService,
            "get_global_pagerank",
            AsyncMock(return_value=[{"name": "Hỏng board STM32", "type": "LifeEvent", "score": 3.4}]),
        ), patch.object(
            GDSService,
            "get_personalized_pagerank",
            AsyncMock(return_value=[{"name": "Áp lực deadline", "type": "Emotion", "score": 2.1}]),
        ), patch.object(
            GDSService,
            "get_critical_bottlenecks",
            AsyncMock(return_value=[{"name": "Thức trắng 72h", "type": "Habit", "score": 5.0}]),
        ), patch.object(
            GDSService,
            "detect_causal_communities",
            AsyncMock(return_value={"Cụm 1 (Đồ án tốt nghiệp)": ["TS. Hùng", "Master"]}),
        ):
            ctx = await GDSService.synthesize_gds_context(user_id=123, entities=["Hỏng board STM32"])
            self.assertIn("<gds_structural_graph_analysis>", ctx)
            self.assertIn("Trọng tâm cấu trúc toàn cục (PageRank)", ctx)
            self.assertIn("Hỏng board STM32", ctx)
            self.assertIn("Tác động lan tỏa nhân quả", ctx)
            self.assertIn("Áp lực deadline", ctx)
            self.assertIn("Mắt xích nút thắt xung yếu (Betweenness Centrality)", ctx)
            self.assertIn("Thức trắng 72h", ctx)
            self.assertIn("Phân cụm nhân quả (Louvain)", ctx)
            self.assertIn("</gds_structural_graph_analysis>", ctx)


if __name__ == "__main__":
    unittest.main()
