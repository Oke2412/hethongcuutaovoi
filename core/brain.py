import logging
import asyncio
from typing import Optional
from mem0 import Memory
from config import settings

logger = logging.getLogger(__name__)


class RaphaelBrain:
    """
    Core AI Brain module. Independent of Telegram or any specific frontend.
    Handles multimodal inputs (text, image) and outputs text responses.
    Maintains long-term memory via Mem0 (ChromaDB + Neo4j GraphRAG).
    """

    def __init__(self) -> None:
        config = {
            "version": "v1.1",
            "llm": {
                "provider": "gemini",
                "config": {
                    "model": "gemini-2.5-flash",
                    "api_key": settings.gemini_api_key,
                },
            },
            "embedder": {
                "provider": "huggingface",
                "config": {
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
            },
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "raphael_memories",
                    "path": "./chroma_db",
                },
            },
            "graph_store": {
                "provider": "neo4j",
                "config": {
                    "url": "neo4j://neo4j:7687",
                    "username": "neo4j",
                    "password": "password",
                },
            },
        }
        self.memory = Memory.from_config(config)

    async def process_input(
        self,
        user_id: str,
        text_content: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        audio_bytes: Optional[bytes] = None,
    ) -> str:
        """Universal entry point for all frontend adapters."""
        from core.llm import generate_response
        from core.omniscience import get_omniscient_state, log_message

        # 1. Log user message to sliding window
        if text_content:
            await log_message(int(user_id), "user", text_content)

        # 2. Multimodal pre-processing
        multimodal_context = ""
        if image_bytes:
            multimodal_context = "[Nguoi dung da gui mot buc anh. Hay xu ly no.]\n"

        final_text = (text_content or "") + ("\n" + multimodal_context if multimodal_context else "")

        # 3. Retrieve long-term memories via Mem0
        # Mem0 v2 API: user_id must be passed via filters={}, NOT as a top-level kwarg
        memory_context = ""
        try:
            mem_results = await asyncio.to_thread(
                self.memory.search,
                query=final_text,
                filters={"user_id": user_id},
                limit=5,
            )
            if mem_results:
                memory_context = "--- KY UC DAI HAN TU MEM0 (GRAPH) ---
"
                for mem in mem_results:
                    # Mem0 v2 uses key "memory"; v1 used "text" — handle both
                    text = mem.get("memory") or mem.get("text") or ""
                    if text:
                        memory_context += f"- {text}
"
        except Exception as exc:
            logger.warning("Mem0 search failed (non-fatal, continuing): %s", exc)

        # 4. Get full Omniscience State snapshot from SQLite
        omniscience_context = await get_omniscient_state(int(user_id))

        # 5. Combine all context layers
        full_context = omniscience_context + "

" + memory_context

        # 6. Call LLM Tool Agent (Raphael)
        response = await generate_response(
            user_id=int(user_id),
            user_context=full_context,
            user_message=final_text,
        )

        # 7. Log assistant response to sliding window
        await log_message(int(user_id), "assistant", response)

        # 8. Persist interaction to Mem0 (non-blocking background task)
        from datetime import datetime
        current_time = datetime.now().isoformat()

        async def _add_to_mem0() -> None:
            try:
                await asyncio.to_thread(
                    self.memory.add,
                    messages=[
                        {"role": "user", "content": final_text},
                        {"role": "assistant", "content": response},
                    ],
                    user_id=user_id,
                    metadata={"timestamp": current_time, "source": "chat"},
                )
            except Exception as exc:
                logger.warning("Mem0 add failed (non-fatal): %s", exc)

        asyncio.create_task(_add_to_mem0())

        return response


# Global singleton — initialized once on bot startup
brain = RaphaelBrain()
