import logging
import asyncio
from typing import Optional, Any
from mem0 import Memory
from config import settings
from datetime import datetime

logger = logging.getLogger(__name__)

class RaphaelBrain:
    def __init__(self) -> None:
        config = {
            "version": "v1.1",
            "llm": {"provider": "gemini", "config": {"model": "models/gemini-3.5-flash-lite", "api_key": settings.gemini_api_key}},
            "embedder": {
                "provider": "gemini",
                "config": {
                    "model": "gemini-embedding-2-preview",
                    "api_key": settings.gemini_api_key,
                },
            },
            "vector_store": {"provider": "chroma", "config": {"collection_name": "raphael_memories", "path": "./chroma_db"}},
            "graph_store": {"provider": "neo4j", "config": {"url": "neo4j://neo4j:7687", "username": "neo4j", "password": "password"}},
        }
        self.memory = Memory.from_config(config)

    async def process_input(
        self,
        user_id: str,
        text_content: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        audio_bytes: Optional[bytes] = None,
    ) -> tuple[str, Any]:
        from core.router import classify_message
        from core.omniscience import get_mini_context, log_message
        from core.llm import run_extraction_step, run_response_step, query_causal_graph
        from core.hud import build_hud

        if text_content:
            await log_message(int(user_id), "user", text_content)

        mini_ctx = await get_mini_context(int(user_id))
        msg_class = classify_message(text_content or "")
        
        if msg_class == "chat" and len((text_content or "").split()) > 20:
            from core.router import semantic_classify
            from core.llm import _get_gemini_client
            msg_class = await semantic_classify(text_content or "", _get_gemini_client())

        
        tool_results, impact_flag, causal_ctx = [], False, ""
        
        async def _add_to_mem0(mem, uid, text):
            try:
                await asyncio.to_thread(
                    mem.add,
                    messages=[
                        {"role": "user", "content": text},
                    ],
                    user_id=uid,
                    metadata={"timestamp": datetime.now().isoformat(), "source": "chat"},
                )
            except Exception as exc:
                logger.warning("Mem0 add failed: %s", exc)

        async def _persist_to_graph(tools, uid):
            # TBD: Actually map tools to neo4j entities
            pass

        if msg_class in ("data", "deep"):
            tool_results, impact_flag = await run_extraction_step(
                int(user_id), text_content or "", mini_ctx
            )
            # Background tasks
            asyncio.create_task(_persist_to_graph(tool_results, int(user_id)))
            asyncio.create_task(_add_to_mem0(self.memory, user_id, text_content or ""))

            if impact_flag:
                entities = [r.get("entity", "") for r in tool_results]
                causal_ctx = await query_causal_graph(int(user_id), entities)

        response = await run_response_step(
            int(user_id), text_content or "", mini_ctx,
            tool_results, impact_flag, causal_ctx
        )

        # Append HUD
        hud_line, keyboard = await build_hud(int(user_id))
        full_response = response + "\n" + hud_line

        await log_message(int(user_id), "assistant", response)
        
        return full_response, keyboard  # We return tuple as requested

brain = RaphaelBrain()
