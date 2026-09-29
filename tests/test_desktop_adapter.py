"""
tests/test_desktop_adapter.py — Automated Tests for Desktop App Adapter.
Tests REST and SSE endpoints: /health, /api/chat (GET and POST), /api/status, and /api/graph/cosmos.
"""

import json
import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestDesktopAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import asyncio
        from db.database import init_db
        asyncio.run(init_db())
    def test_health_check(self):
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")

    def test_chat_get_ping(self):
        """Tests GET /api/chat used by RemoteServerClient.test_connection()."""
        response = client.get("/api/chat")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")

    def test_get_status(self):
        response = client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "online")
        self.assertIn("hud", data)

    def test_get_cosmos_graph(self):
        response = client.get("/api/graph/cosmos")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("nodes", data)
        self.assertIn("links", data)
        self.assertGreaterEqual(len(data["nodes"]), 1)

    @patch("api.routes.desktop.brain.process_input", new_callable=AsyncMock)
    def test_chat_post_json(self, mock_process_input):
        mock_process_input.return_value = (
            "《Báo cáo》 Master đã hoàn thành mục tiêu ngày hôm nay.\n\n━━━━━━━━━━━━━━━━━━━━━\n⚡ 8/10 | 😐 7/10 | ❤️ 9/10 | 💎 150cr | 📍 H3:8928308280fffff",
            None,
        )

        payload = {
            "prompt": "Hôm nay tôi đã hoàn thành xong task",
            "stream": False,
        }
        response = client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(
            data.get("text"), "《Báo cáo》 Master đã hoàn thành mục tiêu ngày hôm nay."
        )
        self.assertIn("⚡ 8/10", data.get("hud"))

    @patch("api.routes.desktop.brain.process_input", new_callable=AsyncMock)
    def test_chat_post_sse_stream(self, mock_process_input):
        mock_process_input.return_value = (
            "《Xác nhận》 Tiến độ đã được ghi nhận, thưa Master.\n\n━━━━━━━━━━━━━━━━━━━━━\n⚡ 8/10 | 😐 7/10 | ❤️ 9/10 | 💎 150cr | 📍 H3:8928308280fffff",
            None,
        )

        payload = {
            "prompt": "Xác nhận báo cáo",
            "stream": True,
        }
        response = client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("content-type"), "text/event-stream; charset=utf-8"
        )

        # Parse SSE stream exactly as RemoteServerClient in tensurafrontend does
        lines = response.text.split("\n")
        tokens = []
        done_received = False

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("data: "):
                line_data = line[6:].strip()
                if line_data == "[DONE]":
                    done_received = True
                    break
                parsed = json.loads(line_data)
                self.assertIn("text", parsed)
                tokens.append(parsed["text"])

        self.assertTrue(done_received, "Stream did not end with [DONE]")
        reconstructed = "".join(tokens).strip()
        self.assertEqual(
            reconstructed, "《Xác nhận》 Tiến độ đã được ghi nhận, thưa Master."
        )

    def test_ambient_transcript_flow(self):
        """Tests POST /api/ambient/transcript and GET /api/ambient/transcripts with FTS5."""
        # 1. Post ambient transcript
        payload = {
            "text": "Master và đồng đội thảo luận về thiết kế mạch ARM cho robot",
            "speaker": "master_and_team",
            "h3_index": "8928308280fffff",
            "extract_to_graph": False,  # disable async neo4j call in unit test
        }
        post_resp = client.post("/api/ambient/transcript", json=payload)
        self.assertEqual(post_resp.status_code, 200)
        post_data = post_resp.json()
        self.assertEqual(post_data.get("status"), "ok")
        transcript_id = post_data.get("id")
        self.assertIsNotNone(transcript_id)

        # 2. Get list of ambient transcripts
        get_resp = client.get("/api/ambient/transcripts")
        self.assertEqual(get_resp.status_code, 200)
        get_data = get_resp.json()
        self.assertEqual(get_data.get("status"), "ok")
        self.assertGreaterEqual(get_data.get("count", 0), 1)

        # 3. Query with FTS5 keyword
        search_resp = client.get("/api/ambient/transcripts?query=robot")
        self.assertEqual(search_resp.status_code, 200)
        search_data = search_resp.json()
        self.assertEqual(search_data.get("status"), "ok")
        matched = [t for t in search_data.get("transcripts", []) if "robot" in t.get("text", "")]
        self.assertGreaterEqual(len(matched), 1)


if __name__ == "__main__":
    unittest.main()
