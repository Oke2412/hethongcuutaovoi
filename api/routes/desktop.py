"""
api/routes/desktop.py — Desktop Application Adapter for Raphael Life OS.
Provides REST and Server-Sent Events (SSE) streaming endpoints for the native desktop overlay
and audio pipeline (tensurafrontend), connecting to RaphaelBrain, SQLite, and Neo4j.
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from config import settings
from core.brain import brain
from core.hud import build_hud
from core.neo4j_client import get_neo4j_driver

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Desktop Adapter"])


class ChatRequest(BaseModel):
    prompt: Optional[str] = Field(default=None, description="Direct text prompt from user")
    messages: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="OpenAI-compatible messages list"
    )
    stream: bool = Field(default=False, description="Enable SSE token streaming")
    user_id: Optional[str] = Field(
        default=None, description="Target user ID (defaults to settings.allowed_user_id)"
    )


@router.get("/chat")
async def chat_health_check() -> JSONResponse:
    """
    Health check and connection verification endpoint for RemoteServerClient.test_connection().
    """
    return JSONResponse(
        {
            "status": "ok",
            "service": "Raphael Core Brain Desktop Adapter",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@router.post("/chat")
async def chat_endpoint(request: ChatRequest) -> Any:
    """
    Core chat endpoint connecting Desktop Voice/UI to RaphaelBrain.process_input().
    Supports both standard JSON and real-time Server-Sent Events (SSE) streaming.
    """
    # 1. Resolve user query
    query_text = ""
    if request.prompt and request.prompt.strip():
        query_text = request.prompt.strip()
    elif request.messages:
        # Extract the last user message
        for msg in reversed(request.messages):
            if msg.get("role") == "user":
                query_text = str(msg.get("content", "")).strip()
                break
        if not query_text and request.messages:
            query_text = str(request.messages[-1].get("content", "")).strip()

    if not query_text:
        raise HTTPException(status_code=400, detail="Missing text prompt or user message.")

    # 2. Resolve target user ID
    uid_str = request.user_id or str(settings.allowed_user_id or 8763843475)

    try:
        # 3. Process via Raphael Core Brain
        response_text, keyboard = await brain.process_input(
            user_id=uid_str, text_content=query_text
        )
    except Exception as exc:
        logger.error(f"Error executing brain.process_input: {exc}", exc_info=True)
        response_text = "《Báo cáo》 Hệ thống máy chủ gặp sự cố khi suy luận."
        keyboard = None

    # 4. Separate spoken response from HUD metrics line
    if "━━━━━━━━━━━━━━━━━━━━━" in response_text:
        spoken_text, hud_part = response_text.split("━━━━━━━━━━━━━━━━━━━━━", 1)
        spoken_text = spoken_text.strip()
        hud_part = "━━━━━━━━━━━━━━━━━━━━━" + hud_part
    else:
        spoken_text = response_text.strip()
        hud_part = ""

    # 5. Handle Streaming Response (SSE for low-latency TTS)
    if request.stream:
        async def sse_generator():
            # Break down response into words/phrases for smooth streaming to TTS
            tokens = re.findall(r"\S+\s*", spoken_text)
            if not tokens:
                tokens = [spoken_text]

            for token in tokens:
                chunk = {
                    "text": token,
                    "response": token,
                    "token": token,
                    "done": False,
                }
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.02)

            # Signal completion according to SSE standard
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            sse_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # 6. Standard JSON Response
    return JSONResponse(
        {
            "status": "ok",
            "text": spoken_text,
            "response": spoken_text,
            "hud": hud_part.strip(),
            "full_response": response_text,
            "has_keyboard": keyboard is not None,
        }
    )


@router.get("/graph/cosmos")
async def get_cosmos_graph(limit: int = 150) -> JSONResponse:
    """
    Returns knowledge graph entities and causal relationships formatted for the
    Desktop App's background Cosmos Constellation canvas.
    """
    driver = get_neo4j_driver()
    if driver is not None:
        try:
            nodes_map: Dict[str, Any] = {}
            links: List[Dict[str, Any]] = []

            async with driver.session() as session:
                result = await session.run(
                    f"MATCH (n)-[r]->(m) RETURN n, r, m LIMIT {limit}"
                )
                async for record in result:
                    n = record["n"]
                    r = record["r"]
                    m = record["m"]

                    n_id = str(
                        getattr(n, "element_id", None)
                        or getattr(n, "id", None)
                        or str(id(n))
                    )
                    m_id = str(
                        getattr(m, "element_id", None)
                        or getattr(m, "id", None)
                        or str(id(m))
                    )

                    n_props = dict(n)
                    m_props = dict(m)
                    n_labels = list(getattr(n, "labels", []))
                    m_labels = list(getattr(m, "labels", []))

                    if n_id not in nodes_map:
                        nodes_map[n_id] = {
                            "id": n_id,
                            "name": n_props.get("name")
                            or (n_labels[0] if n_labels else n_id),
                            "labels": n_labels,
                            "properties": n_props,
                            "val": 10,
                        }
                    if m_id not in nodes_map:
                        nodes_map[m_id] = {
                            "id": m_id,
                            "name": m_props.get("name")
                            or (m_labels[0] if m_labels else m_id),
                            "labels": m_labels,
                            "properties": m_props,
                            "val": 8,
                        }
                    links.append(
                        {
                            "source": n_id,
                            "target": m_id,
                            "type": getattr(r, "type", "RELATED_TO"),
                            "properties": dict(r) if hasattr(r, "keys") else {},
                        }
                    )

            if nodes_map:
                return JSONResponse(
                    {
                        "is_live_db": True,
                        "nodes": list(nodes_map.values()),
                        "links": links,
                    }
                )
        except Exception as exc:
            logger.warning(f"Neo4j cosmos graph query error: {exc}")

    # Graceful celestial fallback constellation for UI rendering
    return JSONResponse(
        {
            "is_live_db": False,
            "nodes": [
                {
                    "id": "raphael",
                    "name": "Raphael (Lord of Wisdom)",
                    "labels": ["System"],
                    "properties": {"role": "Causal AI Core"},
                    "val": 15,
                },
                {
                    "id": "master",
                    "name": "Master (Rimuru)",
                    "labels": ["User"],
                    "properties": {"title": "Host"},
                    "val": 12,
                },
                {
                    "id": "omni_agent",
                    "name": "Omni-Agentic Loop",
                    "labels": ["Skill"],
                    "properties": {"loop": "DeepSeek V4.1"},
                    "val": 10,
                },
                {
                    "id": "causal_rag",
                    "name": "Causal GraphRAG",
                    "labels": ["Memory"],
                    "properties": {"storage": "Neo4j 3-Tier"},
                    "val": 10,
                },
                {
                    "id": "mem0",
                    "name": "Chroma Vector Memory",
                    "labels": ["Memory"],
                    "properties": {"model": "Qwen3-Embedding-8B"},
                    "val": 8,
                },
                {
                    "id": "fts5",
                    "name": "SQLite FTS5 Sparse Search",
                    "labels": ["Database"],
                    "properties": {"engine": "SQLite"},
                    "val": 8,
                },
                {
                    "id": "desktop_adapter",
                    "name": "Desktop Native Adapter",
                    "labels": ["Adapter"],
                    "properties": {"interface": "Electron Overlay"},
                    "val": 9,
                },
            ],
            "links": [
                {"source": "master", "target": "raphael", "type": "PROTECTED_BY"},
                {"source": "raphael", "target": "omni_agent", "type": "OPERATES"},
                {"source": "omni_agent", "target": "causal_rag", "type": "QUERIES"},
                {"source": "omni_agent", "target": "mem0", "type": "SEARCHES"},
                {"source": "omni_agent", "target": "fts5", "type": "INDEXES"},
                {"source": "desktop_adapter", "target": "raphael", "type": "INVOKES"},
            ],
        }
    )


@router.get("/status")
async def get_system_status(user_id: Optional[str] = None) -> JSONResponse:
    """
    Returns current user HUD metrics and active system quests.
    """
    uid = int(user_id or settings.allowed_user_id or 0)
    try:
        hud_line, _ = await build_hud(uid)
    except Exception as exc:
        logger.warning(f"Failed to build HUD for user {uid}: {exc}")
        hud_line = "⚡ ? | 😐 ? | ❤️ ? | 💎 ?cr | 📍 H3:?"

    return JSONResponse(
        {
            "status": "online",
            "user_id": uid,
            "hud": hud_line.replace("━━━━━━━━━━━━━━━━━━━━━\n", "").strip(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
