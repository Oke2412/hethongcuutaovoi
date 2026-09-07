import logging
import asyncio
from typing import Optional, List
from mem0 import Memory
from config import settings

logger = logging.getLogger(__name__)

class RaphaelBrain:
    """
    Core AI Brain module. Completely independent of Telegram or any specific frontend.
    Handles multimodal inputs (text, image, audio) and outputs text responses.
    Maintains long-term memory via Mem0.
    """
    def __init__(self):
        # Configure Mem0 to use Gemini and local ChromaDB
        config = {
            "version": "v1.1",
            "llm": {
                "provider": "litellm",
                "config": {
                    "model": "gemini/gemini-3.8-flash",
                    "api_key": settings.gemini_api_key,
                }
            },
            "embedder": {
                "provider": "gemini",
                "config": {
                    "api_key": settings.gemini_api_key,
                    "model": "models/text-embedding-004"
                }
            },
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "raphael_memories",
                    "path": "./chroma_db"
                }
            },
            "graph_store": {
                "provider": "neo4j",
                "config": {
                    "url": "neo4j://neo4j:7687",
                    "username": "neo4j",
                    "password": "password"
                }
            }
        }
        self.memory = Memory.from_config(config)

    async def process_input(
        self, 
        user_id: str, 
        text_content: Optional[str] = None, 
        image_bytes: Optional[bytes] = None, 
        audio_bytes: Optional[bytes] = None
    ) -> str:
        """
        Universal entry point for all frontend adapters.
        """
        from core.llm import generate_response
        from core.omniscience import get_omniscient_state, log_message
        
        # 1. Log the user message
        if text_content:
            await log_message(int(user_id), "user", text_content)
        
        # 2. Multimodal pre-processing (Extract text from images/audio if present)
        multimodal_context = ""
        if image_bytes:
            multimodal_context += "[Người dùng đã gửi một bức ảnh. Hãy xử lý nó.]\n"
        
        final_text = (text_content or "") + "\n" + multimodal_context
        
        # 3. Retrieve Memories using Mem0
        memories = self.memory.search(query=final_text, user_id=user_id, limit=5)
        memory_context = "--- KÝ ỨC DÀI HẠN TỪ MEM0 (GRAPH) ---\n"
        for mem in memories:
            memory_context += f"- {mem['text']}\n"
            
        # 4. GET OMNISCIENCE STATE
        omniscience_context = await get_omniscient_state(int(user_id))
        
        # Combine contexts
        full_context = omniscience_context + "\n\n" + memory_context
            
        # 5. Call the Core LLM Tool Agent (Raphael) - Default to Flash for chat
        response = await generate_response(
            user_id=int(user_id), 
            user_context=full_context, 
            user_message=final_text
        )
        
        # 6. Log the assistant response
        await log_message(int(user_id), "assistant", response)
        
        # 7. Save the new interaction to Mem0
        from datetime import datetime
        current_time = datetime.now().isoformat()
        
        # We run mem0 add in a separate thread so it doesn't block the async loop
        import asyncio
        asyncio.create_task(
            asyncio.to_thread(
                self.memory.add,
                messages=[{"role": "user", "content": final_text}, {"role": "assistant", "content": response}],
                user_id=user_id,
                metadata={"timestamp": current_time, "source": "chat"}
            )
        )
        
        return response

# Global instance
brain = RaphaelBrain()
