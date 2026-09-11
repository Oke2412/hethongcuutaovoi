import asyncio
import json
import logging
from openai import AsyncOpenAI
from typing import Tuple, List

logger = logging.getLogger(__name__)

SYSTEM_ROUTER = """Phân loại tin nhắn của user và Trích xuất Keywords (Dựa trên cả Ngữ cảnh).

Bạn phải trả về DUY NHẤT một chuỗi JSON hợp lệ với định dạng:
{
  "class": "deep" | "data" | "chat",
  "keywords": ["keyword1", "keyword2"]
}

LUẬT PHÂN LOẠI (class):
- 'deep': Câu lệnh chứa ẩn ý sâu xa, yêu cầu lập kế hoạch phức tạp, phân tích tâm lý/nguyên nhân, VÀ/HOẶC có kèm số liệu. (Deep sẽ gọi Tool trích xuất, soi Graph, và phân tích).
- 'data': Thuần túy là yêu cầu tạo nhiệm vụ, cập nhật số liệu (cân nặng, giấc ngủ, mood), báo cáo tiến độ, hoặc ra lệnh.
- 'chat': Thuần túy là tâm sự phiếm, chitchat, không chứa yêu cầu/số liệu nào cần lưu trữ.

LUẬT TRÍCH XUẤT KEYWORDS (keywords):
- Mở rộng ngữ nghĩa từ câu của user kết hợp với Lịch sử Ngữ cảnh.
- Trả về 3-5 keywords hoặc cụm từ (synonyms, entities) bằng tiếng Việt để dùng cho Search Engine.
- Nếu class là 'chat', keywords có thể rỗng []."""

async def semantic_router_and_expansion(text: str, mini_ctx: str, client: AsyncOpenAI) -> Tuple[str, List[str]]:
    """Returns (msg_class, keywords) using a single context-aware LLM call."""
    prompt = f"[LỊCH SỬ NGỮ CẢNH]\n{mini_ctx}\n\n[TIN NHẮN HIỆN TẠI]\n{text}"
    try:
        response = await client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",
            messages=[
                {"role": "system", "content": SYSTEM_ROUTER},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        result = response.choices[0].message.content.strip()
        if result.startswith("```json"):
            result = result.replace("```json", "").replace("```", "").strip()
            
        data = json.loads(result)
        msg_class = data.get("class", "chat").lower()
        if msg_class not in ["deep", "data", "chat"]:
            msg_class = "chat"
            
        keywords = data.get("keywords", [])
        return msg_class, keywords
    except Exception as exc:
        logger.warning(f"Router & Expansion LLM failed: {exc}")
        return "chat", []
