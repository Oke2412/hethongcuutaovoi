"""
api/routes/desktop.py — Desktop Application Adapter for Raphael Life OS.
Provides REST and Server-Sent Events (SSE) streaming endpoints for the native desktop overlay
and audio pipeline (tensurafrontend), connecting to RaphaelBrain, SQLite, and Neo4j.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlmodel import select
from sqlalchemy import text as sa_text

from config import settings
from core.brain import brain
from core.hud import build_hud
from core.neo4j_client import get_neo4j_driver
from db.database import AsyncSessionLocal
from db.models import AmbientTranscript

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Desktop Adapter"])

#: Heartbeat cadence for the SSE stream. Must stay well under the 60 s idle
#: timeout of most reverse proxies (Nginx / Tailscale / Cloudflare) while still
#: costing nothing when the model is producing tokens.
SSE_HEARTBEAT_SECONDS = 1.0

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def _sse(payload: Dict[str, Any]) -> str:
    """Encode one SSE frame. The double newline is mandatory."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _split_hud(response_text: str) -> tuple[str, str]:
    """Separate the spoken sentence from the trailing HUD metrics line."""
    if "━━━━━━━━━━━━━━━━━━━━━" in response_text:
        spoken_text, hud_part = response_text.split("━━━━━━━━━━━━━━━━━━━━━", 1)
        return spoken_text.strip(), "━━━━━━━━━━━━━━━━━━━━━" + hud_part
    return response_text.strip(), ""


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

    # 3. Streaming path: return the response object immediately and let the
    #    pipeline push phase/tool/reasoning-token events while it thinks. The
    #    previous implementation awaited the full turn (≈20 s of silence) and
    #    then replayed the finished sentence word by word.
    if request.stream:
        return StreamingResponse(
            _raphael_event_stream(uid_str, query_text),
            media_type="text/event-stream",
            headers=SSE_HEADERS,
        )

    thinking_text = ""
    try:
        # 4. Process via Raphael Core Brain with Metacognition
        res = await brain.process_input(
            user_id=uid_str, text_content=query_text, return_thinking=True
        )
        if len(res) == 3:
            response_text, keyboard, thinking_text = res
        else:
            response_text, keyboard = res
    except Exception as exc:
        logger.error(f"Error executing brain.process_input: {exc}", exc_info=True)
        response_text = "《Báo cáo》 Hệ thống máy chủ gặp sự cố khi suy luận."
        keyboard = None

    # 5. Separate spoken response from HUD metrics line
    spoken_text, hud_part = _split_hud(response_text)

    # 6. Standard JSON Response with Metacognition Thinking field
    return JSONResponse(
        {
            "status": "ok",
            "text": spoken_text,
            "response": spoken_text,
            "thinking": thinking_text,
            "hud": hud_part.strip(),
            "full_response": response_text,
            "has_keyboard": keyboard is not None,
        }
    )


async def _raphael_event_stream(user_id: str, query_text: str) -> AsyncIterator[str]:
    """Bridge the brain turn to SSE.

    The turn runs as an independent task that pushes progress into a queue; this
    generator drains the queue and injects heartbeats while the model reasons, so
    the client never sees a silent socket. Client disconnect stops *streaming*
    but not the turn — state writes and metacognition logging must still land.
    """
    queue: asyncio.Queue = asyncio.Queue()
    started = time.perf_counter()

    def elapsed_ms() -> int:
        return int((time.perf_counter() - started) * 1000)

    async def sink(event: Dict[str, Any]) -> None:
        await queue.put(event)

    async def runner() -> None:
        try:
            res = await brain.process_input(
                user_id=user_id,
                text_content=query_text,
                return_thinking=True,
                on_event=sink,
            )
            if len(res) == 3:
                response_text, keyboard, thinking_text = res
            else:
                response_text, keyboard = res
                thinking_text = ""
            spoken_text, hud_part = _split_hud(response_text)
            await queue.put(
                {
                    "type": "final",
                    "text": spoken_text,
                    "response": spoken_text,
                    "thinking": thinking_text,
                    "hud": hud_part.strip(),
                    "full_response": response_text,
                    "has_keyboard": keyboard is not None,
                    "elapsed_ms": elapsed_ms(),
                }
            )
        except Exception as exc:
            logger.error(f"Streaming turn failed: {exc}", exc_info=True)
            await queue.put(
                {
                    "type": "error",
                    "message": "《Báo cáo》 Hệ thống máy chủ gặp sự cố khi suy luận.",
                    "elapsed_ms": elapsed_ms(),
                }
            )
        finally:
            await queue.put(None)

    task = asyncio.create_task(runner())

    try:
        yield _sse({"type": "open", "elapsed_ms": 0})
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=SSE_HEARTBEAT_SECONDS)
            except asyncio.TimeoutError:
                yield _sse({"type": "heartbeat", "elapsed_ms": elapsed_ms()})
                continue
            if event is None:
                break
            yield _sse(event)
        yield "data: [DONE]\n\n"
    finally:
        # Never cancel the turn: the scribe pass and metacognition writes own it.
        if not task.done():
            task.add_done_callback(lambda t: t.cancelled() or t.exception())


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


class AmbientTranscriptRequest(BaseModel):
    text: str = Field(description="Raw transcribed ambient audio chunk from Native App")
    speaker: Optional[str] = Field(default="ambient", description="Speaker identity or ambient tag")
    h3_index: Optional[str] = Field(default="", description="Optional Uber H3 spatial index")
    user_id: Optional[str] = Field(default=None, description="User ID (defaults to allowed_user_id)")
    extract_to_graph: bool = Field(default=True, description="Whether to trigger async Neo4j extraction")


async def _extract_ambient_to_graph_task(transcript_id: int, user_id: int, text_content: str, h3_index: str) -> None:
    """Asynchronously extract entities and causal links from ambient transcript and inject into Neo4j."""
    try:
        from scripts.ingest_text import extract_graph, inject_to_neo4j
        json_data = await extract_graph(text_content)
        if json_data and isinstance(json_data, dict):
            # Inject to Neo4j with pointer linking back to SQLite transcript ID
            await inject_to_neo4j(json_data, source_transcript_id=transcript_id)

            # Mark as extracted in SQLite
            async with AsyncSessionLocal() as session:
                record = await session.get(AmbientTranscript, transcript_id)
                if record:
                    record.is_extracted = True
                    nodes = json_data.get("nodes", [])
                    record.extracted_summary = f"{len(nodes)} entities extracted"
                    session.add(record)
                    await session.commit()
            logger.info(f"Successfully extracted ambient transcript #{transcript_id} to Neo4j.")
    except Exception as exc:
        logger.warning(f"Async ambient graph extraction failed for #{transcript_id}: {exc}")


@router.post("/ambient/transcript")
async def record_ambient_transcript(request: AmbientTranscriptRequest) -> JSONResponse:
    """
    Ingests an ambient audio transcript from Raphael App.
    Saves the full raw text in SQLite with FTS5 indexing, and schedules background Causal Graph extraction into Neo4j with pointer linking.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Empty transcript text.")

    uid = int(request.user_id or settings.allowed_user_id or 0)

    try:
        record = AmbientTranscript(
            user_id=uid,
            text=request.text.strip(),
            speaker=request.speaker or "ambient",
            h3_index=request.h3_index or "",
            recorded_at=datetime.now(timezone.utc),
            is_extracted=False,
        )
        async with AsyncSessionLocal() as session:
            session.add(record)
            await session.commit()
            await session.refresh(record)

        # Trigger background Causal Graph extraction if requested
        if request.extract_to_graph:
            asyncio.create_task(
                _extract_ambient_to_graph_task(
                    transcript_id=record.id,
                    user_id=uid,
                    text_content=record.text,
                    h3_index=record.h3_index,
                )
            )

        return JSONResponse(
            {
                "status": "ok",
                "id": record.id,
                "recorded_at": record.recorded_at.isoformat(),
                "message": "Ambient transcript recorded. Causal extraction scheduled.",
            }
        )
    except Exception as exc:
        logger.error(f"Error saving ambient transcript: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error saving transcript.")


@router.get("/ambient/transcripts")
async def get_ambient_transcripts(
    query: Optional[str] = None,
    limit: int = 20,
    user_id: Optional[str] = None,
) -> JSONResponse:
    """
    Retrieves ambient transcripts. Supports FTS5 keyword full-text search when query parameter is provided.
    """
    uid = int(user_id or settings.allowed_user_id or 0)
    try:
        async with AsyncSessionLocal() as session:
            if query and query.strip():
                # FTS5 search
                safe_query = query.strip().replace('"', '""')
                stmt = sa_text("""
                    SELECT at.id, at.user_id, at.text, at.speaker, at.h3_index, at.recorded_at, at.is_extracted, at.extracted_summary
                    FROM ambienttranscript at
                    JOIN ambienttranscript_fts fts ON at.id = fts.id
                    WHERE ambienttranscript_fts MATCH :q AND (:uid = 0 OR at.user_id = :uid)
                    ORDER BY at.recorded_at DESC
                    LIMIT :limit
                """)
                result = await session.execute(stmt, {"q": f'"{safe_query}"', "uid": uid, "limit": limit})
                rows = result.fetchall()
                data = [
                    {
                        "id": r[0],
                        "user_id": r[1],
                        "text": r[2],
                        "speaker": r[3],
                        "h3_index": r[4],
                        "recorded_at": str(r[5]),
                        "is_extracted": bool(r[6]),
                        "extracted_summary": r[7],
                    }
                    for r in rows
                ]
            else:
                stmt_select = select(AmbientTranscript)
                if uid > 0:
                    stmt_select = stmt_select.where(AmbientTranscript.user_id == uid)
                stmt_select = stmt_select.order_by(AmbientTranscript.recorded_at.desc()).limit(limit)
                records = (await session.execute(stmt_select)).scalars().all()
                data = [
                    {
                        "id": r.id,
                        "user_id": r.user_id,
                        "text": r.text,
                        "speaker": r.speaker,
                        "h3_index": r.h3_index,
                        "recorded_at": r.recorded_at.isoformat(),
                        "is_extracted": r.is_extracted,
                        "extracted_summary": r.extracted_summary,
                    }
                    for r in records
                ]

        return JSONResponse({"status": "ok", "count": len(data), "transcripts": data})
    except Exception as exc:
        logger.error(f"Error querying ambient transcripts: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error querying transcripts.")
