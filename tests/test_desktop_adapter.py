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


if __name__ == "__main__":
    unittest.main()
