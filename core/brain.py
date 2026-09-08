import logging
import asyncio
from typing import Optional
from mem0 import Memory
from config import settings

logger = logging.getLogger(__name__)


class RaphaelBrain:
    def __init__(self) -> None:
        config = {
            "version": "v1.1",
            "llm": {"provider": "gemini", "config": {"model": "models/gemini-3.5-flash-lite", "api_key": settings.gemini_api_key}},
            "embedder": {"provider": "huggingface", "config": {"model": "sentence-transformers/all-MiniLM-L6-v2"}},
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
    ) -> str:
        from core.llm import generate_response
        from core.omniscience import get_omniscient_state, log_message
        from datetime import datetime

        if text_content:
            await log_message(int(user_id), "user", text_content)

        multimodal_context = ""
        if image_bytes:
            multimodal_context = "[Nguoi dung gui anh.]" + chr(10)

        final_text = (text_content or "") + (chr(10) + multimodal_context if multimodal_context else "")

        memory_context = ""
        try:
            mem_results = await asyncio.to_thread(
                self.memory.search,
                query=final_text,
                filters={"user_id": user_id},
                limit=5,
            )
            if mem_results:
                memory_context = "--- KY UC MEM0 ---" + chr(10)
                for mem in mem_results:
                    if isinstance(mem, dict):
                        text = mem.get("memory") or mem.get("text") or ""
                    else:
                        text = str(mem)
                    
                    if text:
                        memory_context += "- " + text + chr(10)
        except Exception as exc:
            logger.warning("Mem0 search failed: %s", exc)

        omniscience_context = await get_omniscient_state(int(user_id))
        full_context = omniscience_context + chr(10) * 2 + memory_context

        response = await generate_response(
            user_id=int(user_id),
            user_context=full_context,
            user_message=final_text,
        )

        await log_message(int(user_id), "assistant", response)

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
                logger.warning("Mem0 add failed: %s", exc)

        asyncio.create_task(_add_to_mem0())
        return response


brain = RaphaelBrain()
