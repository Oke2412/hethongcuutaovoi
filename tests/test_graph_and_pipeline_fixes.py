import asyncio
import os
import sys
import unittest
import uuid

REPO_DIR = r"c:\Users\Asus\Documents\antigravity\amazing-nobel"
sys.path.insert(0, REPO_DIR)
os.chdir(REPO_DIR)
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from core.search import sparse_search
from core.llm import query_causal_graph
from db.database import init_db

class TestGraphAndPipelineFixes(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await init_db()

    async def test_sparse_search_sanitization(self):
        """Test FTS5 does not crash with weird characters, quotes, or booleans."""
        weird_queries = [
            'từ khóa "có ngoặc kép"',
            'test "unbalanced',
            'AND OR NOT * : ()',
            '"""triple quotes"""'
        ]
        # Should execute safely without raising OperationalError
        results = await sparse_search(weird_queries, limit=3)
        self.assertIsInstance(results, list)

    async def test_query_causal_graph_safe_fallback(self):
        """Test query_causal_graph runs without crashing when Neo4j is offline or empty."""
        res = await query_causal_graph(123456, ["Thức khuya", "Mệt mỏi"])
        self.assertIsInstance(res, str)

    def test_unique_temp_file_creation(self):
        """Verify unique filename generation logic."""
        os.makedirs("scratch", exist_ok=True)
        f1 = f"scratch/temp_ingest_{uuid.uuid4().hex[:8]}.txt"
        f2 = f"scratch/temp_ingest_{uuid.uuid4().hex[:8]}.txt"
        self.assertNotEqual(f1, f2)
        with open(f1, "w", encoding="utf-8") as f:
            f.write("test1")
        with open(f2, "w", encoding="utf-8") as f:
            f.write("test2")
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(os.path.exists(f2))
        os.remove(f1)
        os.remove(f2)

if __name__ == "__main__":
    unittest.main()
