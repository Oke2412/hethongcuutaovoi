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
        
        # 1. Multimodal pre-processing (Extract text from images/audio if present)
        multimodal_context = ""
        if image_bytes:
            # Future: use Gemini to analyze image and return text description
            multimodal_context += "[Người dùng đã gửi một bức ảnh. Hãy xử lý nó.]\n"
        
        final_text = (text_content or "") + "\n" + multimodal_context
        
        # 2. Retrieve Memories using Mem0
        # Mem0 searches the local ChromaDB for relevant past context
        memories = self.memory.search(query=final_text, user_id=user_id, limit=5)
        memory_context = "--- KÝ ỨC DÀI HẠN TỪ MEM0 ---\n"
        for mem in memories:
            memory_context += f"- {mem['text']}\n"
            
        # 3. Call the Core LLM Tool Agent (Raphael)
        # We pass the memory context along with the user's message
        response = await generate_response(
            user_id=int(user_id), 
            user_context=memory_context, 
            user_message=final_text
        )
        
        # 4. Save the new interaction to Mem0
        # Mem0 automatically extracts core facts and saves them
        from datetime import datetime
        current_time = datetime.now().isoformat()
        
        self.memory.add(
            messages=[{"role": "user", "content": final_text}, {"role": "assistant", "content": response}], 
            user_id=user_id,
            metadata={"timestamp": current_time}
        )
        
        return response

# Global instance
brain = RaphaelBrain()
