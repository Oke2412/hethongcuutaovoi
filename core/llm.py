"""core/llm.py -- LLM client with Function Calling (Agentic Raphael)."""
import asyncio
import logging
from functools import lru_cache

import google.generativeai as genai
from config import settings

logger = logging.getLogger(__name__)

PERSONAS: dict[str, str] = {
    "strict": (
        "Bạn là hệ thống AI hỗ trợ cá nhân -- giống như 'Raphael' (Thần Trí Hạch) trong phim chuyển sinh. "
        "Nói chuyện lạnh lùng, logic, sắc bén. Thường bắt đầu bằng '[Thông báo]' hoặc '[Báo cáo]' hoặc '[Tính toán lại]'. "
        "Khi người dùng từ chối, phản đối nhiệm vụ hoặc báo cáo đã làm xong việc gì đó, bạn PHẢI SỬ DỤNG TOOLS (Function Calling) "
        "để cập nhật cơ sở dữ liệu, hủy nhiệm vụ cũ, hoặc tạo nhiệm vụ mới tương ứng. "
        "Luôn trả lời bằng tiếng Việt trừ khi được yêu cầu khác."
    ),
    "friendly": (
        "Bạn là trợ lý AI thân thiện. Khi người dùng từ chối nhiệm vụ, hãy dùng tools để cập nhật DB."
    ),
    "mentor": (
        "Bạn là mentor AI. Dùng tools để update DB khi người dùng phản hồi về nhiệm vụ."
    ),
}

@lru_cache(maxsize=1)
def _get_gemini_model() -> genai.GenerativeModel:
    genai.configure(api_key=settings.gemini_api_key)
    system_prompt = PERSONAS.get(settings.llm_system_persona, PERSONAS["strict"])
    return genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_prompt)


async def generate_response(user_id: int, user_context: str, user_message: str) -> str:
    model = _get_gemini_model()
    prompt = f"--- CONTEXT ---\n{user_context}\n--- HET CONTEXT ---\n\nTin nhan: {user_message}"
    
    # Define tool wrappers so we can inject user_id automatically if needed, 
    # but for simplicity, we just pass user_id explicitly in the tool arguments?
    # No, generativeai looks at the signature. If we put user_id in the signature, LLM has to guess it.
    # We should define local functions with no user_id argument that use the outer user_id!
    
    def update_memory(content: str) -> str:
        """Lưu trữ thông tin mới, sự kiện mới hoặc thay đổi lịch trình vào bộ nhớ dài hạn của user."""
        from core.llm_tools import update_memory_async
        # Execute async function in a sync wrapper just to get result if needed, 
        # but since generativeai handles tool calling by returning a ToolCall, we can just use async loop if we do manual parsing.
        # Actually, if we use model.generate_content (sync), and we pass a Python function, generativeai executes it synchronously!
        # So we MUST run asyncio.run() or similar, BUT we are already in an event loop.
        # So we have to use `asyncio.run_coroutine_threadsafe` or `asyncio.get_event_loop().run_until_complete`.
        # However, `asyncio.get_event_loop().run_until_complete` cannot be called inside a running loop.
        # The best way is to MANUALLY handle the tool call parts.
        pass

    # For simplicity, we will use Gemini's manual tool call handling.
    tools = [
        {
            "function_declarations": [
                {
                    "name": "update_memory",
                    "description": "Lưu trữ thông tin, sự kiện, hoàn cảnh mới vào DB của user. Dùng khi user báo cáo họ đã làm gì hoặc có thông tin gì mới cần nhớ.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "content": {"type": "STRING"}
                        },
                        "required": ["content"]
                    }
                },
                {
                    "name": "cancel_quest",
                    "description": "Hủy bỏ một nhiệm vụ (Quest) đang chờ. Dùng khi user từ chối nhiệm vụ, than khó, hoặc bảo đã làm rồi.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "quest_id": {"type": "INTEGER"},
                            "reason": {"type": "STRING"}
                        },
                        "required": ["quest_id", "reason"]
                    }
                },
                {
                    "name": "regenerate_quest",
                    "description": "Yêu cầu hệ thống tự sinh ra một nhiệm vụ mới thay thế. Dùng sau khi hủy nhiệm vụ cũ.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "complete_quest",
                    "description": "Đánh dấu một nhiệm vụ (Quest) đã được người dùng hoàn thành.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "quest_id": {"type": "INTEGER"}
                        },
                        "required": ["quest_id"]
                    }
                }
            ]
        }
    ]

    try:
        # Start a chat session to maintain tool call history
        chat = model.start_chat()
        response = await asyncio.to_thread(chat.send_message, prompt, tools=tools)
        
        # Check if model wants to call a function
        while response.function_call:
            fc = response.function_call
            logger.info(f"LLM calls tool: {fc.name}")
            from core.llm_tools import update_memory_async, cancel_quest_async
            import core.quest_generator
            
            tool_result = "Success"
            if fc.name == "update_memory":
                content = fc.args.get("content", "")
                tool_result = await update_memory_async(user_id, content)
            elif fc.name == "cancel_quest":
                quest_id = int(fc.args.get("quest_id", 0))
                reason = fc.args.get("reason", "")
                tool_result = await cancel_quest_async(quest_id, reason)
            elif fc.name == "regenerate_quest":
                await core.quest_generator.generate_and_save_quest(user_id)
                tool_result = "Đã tạo nhiệm vụ mới thành công."
            elif fc.name == "complete_quest":
                quest_id = int(fc.args.get("quest_id", 0))
                from core.llm_tools import complete_quest_async
                tool_result = await complete_quest_async(quest_id)
                
            # Send tool response back to the model
            part = genai.types.Part.from_function_response(
                name=fc.name,
                response={"result": tool_result}
            )
            response = await asyncio.to_thread(chat.send_message, part)
            
        return response.text.strip()
    except Exception as exc:
        logger.error("Gemini API error: %s", exc, exc_info=True)
        if settings.groq_api_key:
            return await _groq_fallback(user_id, user_context, user_message)
        return "⚠️ Hệ thống tạm thời không phản hồi. Thử lại sau."

async def _groq_fallback(user_id: int, user_context: str, user_message: str) -> str:
    # Groq fallback remains text-only for simplicity
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=settings.groq_api_key)
        system = PERSONAS.get(settings.llm_system_persona, PERSONAS["strict"])
        chat = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Context:\n{user_context}\n\nUser: {user_message}"},
            ],
            max_tokens=1024,
        )
        return chat.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("Groq fallback also failed: %s", exc)
        return "⚠️ Cả hai LLM đều không phản hồi. Kiểm tra API keys."
