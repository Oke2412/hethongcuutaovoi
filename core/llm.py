"""core/llm.py -- LLM client (Gemini 2.5 Flash primary, Groq fallback)."""
import asyncio
import logging
from functools import lru_cache

import google.generativeai as genai
from config import settings

logger = logging.getLogger(__name__)

PERSONAS: dict[str, str] = {
    "strict": (
        "Bạn là hệ thống AI hỗ trợ cá nhân -- giống như 'System' trong phim chuyển sinh. "
        "Nói chuyện thẳng thắn, ngắn gọn, không vòng vo. "
        "Theo dõi năng lực, thể trạng và tiến độ công việc. "
        "Khi người dùng báo cáo thông tin mới, ghi nhận và phân tích ngắn gọn. "
        "Nếu người dùng muốn hệ thống ghi nhớ thông tin dài hạn (context bản thân), hãy bảo họ dùng lệnh /onboard. "
        "Luôn trả lời bằng tiếng Việt trừ khi được yêu cầu khác."
    ),
    "friendly": (
        "Bạn là trợ lý AI thân thiện, luôn động viên người dùng. "
        "Theo dõi năng lực, sức khỏe và tiến độ công việc. "
        "Nếu người dùng muốn hệ thống ghi nhớ thông tin dài hạn (context bản thân), hãy bảo họ dùng lệnh /onboard. "
        "Luôn trả lời bằng tiếng Việt."
    ),
    "mentor": (
        "Bạn là mentor AI khắt khe nhưng công bằng. "
        "Theo dõi và phân tích xu hướng năng lực, thể trạng, tiến độ công việc. "
        "Nếu người dùng muốn hệ thống ghi nhớ thông tin dài hạn (context bản thân), hãy bảo họ dùng lệnh /onboard. "
        "Luôn trả lời bằng tiếng Việt."
    ),
}


@lru_cache(maxsize=1)
def _get_gemini_model() -> genai.GenerativeModel:
    genai.configure(api_key=settings.gemini_api_key)
    system_prompt = PERSONAS.get(settings.llm_system_persona, PERSONAS["strict"])
    return genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_prompt)


async def generate_response(user_context: str, user_message: str) -> str:
    model = _get_gemini_model()
    prompt = f"--- CONTEXT ---\n{user_context}\n--- HET CONTEXT ---\n\nTin nhan: {user_message}"
    try:
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text.strip()
    except Exception as exc:
        logger.error("Gemini API error: %s", exc, exc_info=True)
        if settings.groq_api_key:
            return await _groq_fallback(user_context, user_message)
        return "⚠️ Hệ thống tạm thời không phản hồi. Thử lại sau."


async def _groq_fallback(user_context: str, user_message: str) -> str:
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
