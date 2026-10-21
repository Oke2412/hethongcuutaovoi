---
name: fastapi-sse-streaming
description: >-
  Patterns, protocols, and performance optimization for Server-Sent Events (SSE)
  and token streaming in FastAPI backends. Use this skill when implementing real-time
  LLM text streaming, audio token delivery for Text-to-Speech (TTS), handling client
  disconnects, configuring CORS, or building reactive desktop event bridges.
---

# FastAPI Server-Sent Events (SSE) Streaming Guide

This skill provides standardized implementations for streaming LLM tokens, TTS audio phrases, and system state updates from FastAPI backends to desktop/web frontends with zero buffer blocking.

---

## 1. Mandatory SSE Headers

When serving `text/event-stream`, always set proxy-bypass headers to avoid reverse-proxy buffering (especially Nginx, Cloudflare, or Tailscale):

```python
headers = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",  # Disables proxy buffering in Nginx
    "Content-Type": "text/event-stream",
}
```

---

## 2. Production SSE Endpoint Implementation

```python
import asyncio
import json
import re
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/v1")

@router.post("/chat/stream")
async def stream_chat_response(text: str):
    async def event_generator():
        try:
            # Tokenize or stream word-by-word for natural TTS playback
            tokens = re.findall(r"\S+\s*", text)
            
            for token in tokens:
                payload = {
                    "token": token,
                    "text": token,
                    "done": False,
                }
                # Double newline is mandatory in SSE standard
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.02)  # Natural token cadence
                
            # Signal stream completion
            yield "data: [DONE]\n\n"
        except asyncio.CancelledError:
            # Client disconnected mid-stream
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

---

## 3. Frontend Client Consumption (JavaScript / Tauri / Web)

```javascript
const response = await fetch("/api/v1/chat/stream", { method: "POST", ... });
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value);
    const lines = chunk.split("\n\n");
    for (const line of lines) {
        if (line.startsWith("data: ")) {
            const raw = line.slice(6);
            if (raw === "[DONE]") return;
            const data = JSON.parse(raw);
            renderToken(data.token);
        }
    }
}
```
