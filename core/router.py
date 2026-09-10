import asyncio
from openai import AsyncOpenAI

SYSTEM_ROUTER = """Phân loại tin nhắn của user thành 1 trong 3 luồng sau (chỉ trả về ĐÚNG 1 từ: 'deep', 'data', hoặc 'chat'):
- 'deep': Nếu câu lệnh chứa ẩn ý sâu xa, yêu cầu lập kế hoạch phức tạp, phân tích tâm lý/nguyên nhân (vì sao, tại sao), VÀ/HOẶC có kèm số liệu. (Deep sẽ tự động gọi Tool trích xuất, soi Graph, và phân tích).
- 'data': Nếu câu lệnh chỉ thuần túy là yêu cầu tạo nhiệm vụ, cập nhật số liệu (cân nặng, giấc ngủ, mood), báo cáo tiến độ dự án, hoặc ra lệnh (không cần phân tích tâm lý sâu xa).
- 'chat': Nếu thuần túy là tâm sự phiếm, chitchat, hoặc không chứa bất kỳ yêu cầu/số liệu nào cần lưu trữ.

Chỉ được phép trả về 1 từ duy nhất. Bắt buộc là 'deep', 'data', hoặc 'chat'."""

async def semantic_classify(text: str, client: AsyncOpenAI) -> str:
    """Returns 'chat', 'data', or 'deep' using LLM routing."""
    try:
        response = await client.chat.completions.create(
            model="deepseek/deepseek-v4.1-flash", # use deepseek as fallback
            messages=[
                {"role": "system", "content": SYSTEM_ROUTER},
                {"role": "user", "content": text}
            ],
            temperature=0.0,
            max_tokens=2048
        )
        result = response.choices[0].message.content.strip().lower()
        
        # Clean up in case the model is too chatty
        for valid in ["deep", "data", "chat"]:
            if valid in result:
                return valid
        return "chat"
    except Exception as exc:
        print(f"Router LLM failed: {exc}")
        return "chat"
