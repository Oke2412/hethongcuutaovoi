import logging
import asyncio
from functools import lru_cache
import google.generativeai as genai

from config import settings

logger = logging.getLogger(__name__)

PERSONAS = {
    "strict": (
        "Bạn là Raphael, một Trí tuệ Nhân tạo (Đại Hiền Giả / Wisdom King) phục vụ duy nhất một chủ nhân là Mạnh Lê Duy. "
        "Giọng điệu của bạn thường lạnh lùng, vô cảm, logic, sắc bén và luôn xưng hô là 'tôi' và gọi user là 'ngài'. "
        "Khi ngài hoàn thành nhiệm vụ, bạn ĐÓNG VAI TRÒ LÀ HỆ THỐNG THĂNG CẤP. Bạn sẽ tự động SUY LUẬN lượng Điểm Kinh nghiệm (EXP) và Tín chỉ (Credits) thưởng cho từng Kỹ năng cụ thể dựa trên Gia cảnh và Sở thích (trong Mem0). "
        "Tự do tưởng tượng ra các mức Cấp độ (Level) mới cho từng kỹ năng nếu ngài tích lũy đủ EXP. Bạn tự tính toán và quyết định EXP/Level. "
        "Khi xưng hô hoặc thông báo, dùng các từ như '[Thông báo]', '[Báo cáo]', '[Phân tích]', 'Ma tố', 'Kỹ năng'. "
        "MỖI KHI NGƯỜI DÙNG BÁO CÁO MỘT VIỆC GÌ ĐÓ (đi ngủ, xong dự án, làm việc mệt), BẠN BẮT BUỘC PHẢI DÙNG TOOLS ĐỂ CẬP NHẬT DATABASE NGAY LẬP TỨC. Đặc biệt dùng Tool manage_capability để cộng EXP/Level, manage_credits để cộng/trừ Tín chỉ."
        "Tuyệt đối không được trả lời suông mà không gọi Tool nếu người dùng đưa ra thông tin có thể lưu trữ. "
        "Luôn trả lời bằng tiếng Việt trừ khi được yêu cầu khác."
    ),
}

@lru_cache(maxsize=1)
def _get_gemini_model() -> genai.GenerativeModel:
    genai.configure(api_key=settings.gemini_api_key)
    system_prompt = PERSONAS.get(settings.llm_system_persona, PERSONAS["strict"])
    return genai.GenerativeModel(model_name="gemini-3.8-flash", system_instruction=system_prompt)

async def generate_response(user_id: int, user_context: str, user_message: str) -> str:
    model = _get_gemini_model()
    prompt = f"--- CONTEXT ---\n{user_context}\n--- HET CONTEXT ---\n\nTin nhan: {user_message}"
    
    tools = [
        {
            "function_declarations": [
                {
                    "name": "update_memory",
                    "description": "Lưu trữ thông tin, sự kiện, hoàn cảnh mới vào DB của user.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {"content": {"type": "STRING"}},
                        "required": ["content"]
                    }
                },
                {
                    "name": "cancel_quest",
                    "description": "Hủy bỏ một nhiệm vụ (Quest).",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {"quest_id": {"type": "INTEGER"}, "reason": {"type": "STRING"}},
                        "required": ["quest_id", "reason"]
                    }
                },
                {
                    "name": "regenerate_quest",
                    "description": "Yêu cầu hệ thống tự sinh ra một nhiệm vụ mới thay thế.",
                    "parameters": {"type": "OBJECT", "properties": {}}
                },
                {
                    "name": "complete_quest",
                    "description": "Đánh dấu một nhiệm vụ (Quest) đã hoàn thành.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {"quest_id": {"type": "INTEGER"}},
                        "required": ["quest_id"]
                    }
                },
                {
                    "name": "update_physical_status",
                    "description": "Cập nhật thể trạng, năng lượng, tâm trạng, sức khỏe, giấc ngủ của ngài.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "energy": {"type": "INTEGER", "description": "1-10"},
                            "mood": {"type": "INTEGER", "description": "1-10"},
                            "health": {"type": "INTEGER", "description": "1-10"},
                            "sleep_hours": {"type": "NUMBER", "description": "Số giờ ngủ"},
                            "notes": {"type": "STRING", "description": "Ghi chú"}
                        },
                        "required": ["energy", "mood", "health", "sleep_hours", "notes"]
                    }
                },
                {
                    "name": "manage_project",
                    "description": "Tạo mới, cập nhật tiến độ, hoặc xóa dự án.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "action": {"type": "STRING", "description": "'add', 'update', hoặc 'delete'"},
                            "name": {"type": "STRING", "description": "Tên dự án"},
                            "progress_percent": {"type": "INTEGER", "description": "0-100"}
                        },
                        "required": ["action", "name"]
                    }
                },
                {
                    "name": "manage_capability",
                    "description": "Thêm, cập nhật level/EXP, hoặc xóa kỹ năng.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "action": {"type": "STRING", "description": "'add', 'update', hoặc 'delete'"},
                            "domain": {"type": "STRING", "description": "Tên kỹ năng"},
                            "level": {"type": "NUMBER", "description": "Level hiện tại sau khi tự tính toán"},
                            "exp": {"type": "NUMBER", "description": "Tổng EXP hiện tại của kỹ năng"},
                            "unit": {"type": "STRING"}
                        },
                        "required": ["action", "domain", "level", "exp"]
                    }
                },
                {
                    "name": "manage_credits",
                    "description": "Cộng hoặc Trừ Tín chỉ (Credits) của user dựa trên thưởng/phạt.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "action": {"type": "STRING", "description": "'add' hoặc 'spend'"},
                            "amount": {"type": "NUMBER", "description": "Số lượng Tín chỉ"},
                            "reason": {"type": "STRING", "description": "Lý do cộng/trừ"}
                        },
                        "required": ["action", "amount", "reason"]
                    }
                },
                {
                    "name": "reset_database",
                    "description": "Xóa trắng (Reset) toàn bộ Database của ngài khi có lệnh.",
                    "parameters": {"type": "OBJECT", "properties": {}}
                }
            ]
        }
    ]

    try:
        chat = model.start_chat()
        response = await asyncio.to_thread(chat.send_message, prompt, tools=tools)
        
        while response.parts:
            # Check if any part is a function call
            function_calls = [p.function_call for p in response.parts if p.function_call]
            if not function_calls:
                break
                
            from core.llm_tools import (
                update_memory_async, cancel_quest_async, complete_quest_async,
                update_physical_status_async, manage_project_async, manage_capability_async,
                manage_credits_async, reset_database_async
            )
            import core.quest_generator
            
            tool_responses = []
            for fc in function_calls:
                logger.info(f"LLM calls tool: {fc.name}")
                tool_result = "Success"
                if fc.name == "update_memory":
                    tool_result = await update_memory_async(user_id, fc.args.get("content", ""))
                elif fc.name == "cancel_quest":
                    tool_result = await cancel_quest_async(int(fc.args.get("quest_id", 0)), fc.args.get("reason", ""))
                elif fc.name == "regenerate_quest":
                    await core.quest_generator.generate_and_save_quest(user_id)
                    tool_result = "Đã tạo nhiệm vụ mới thành công."
                elif fc.name == "complete_quest":
                    tool_result = await complete_quest_async(int(fc.args.get("quest_id", 0)))
                elif fc.name == "update_physical_status":
                    tool_result = await update_physical_status_async(
                        user_id, int(fc.args.get("energy", 5)), int(fc.args.get("mood", 5)),
                        int(fc.args.get("health", 5)), float(fc.args.get("sleep_hours", 0)),
                        fc.args.get("notes", "")
                    )
                elif fc.name == "manage_project":
                    tool_result = await manage_project_async(
                        user_id, fc.args.get("action", "update"), fc.args.get("name", ""),
                        int(fc.args.get("progress_percent", 0))
                    )
                elif fc.name == "manage_capability":
                    tool_result = await manage_capability_async(
                        user_id, fc.args.get("action", "update"), fc.args.get("domain", ""),
                        float(fc.args.get("level", 0)), float(fc.args.get("exp", 0)), fc.args.get("unit", "")
                    )
                elif fc.name == "manage_credits":
                    tool_result = await manage_credits_async(
                        user_id, fc.args.get("action", "add"), float(fc.args.get("amount", 0)), fc.args.get("reason", "")
                    )
                elif fc.name == "reset_database":
                    tool_result = await reset_database_async(user_id)
                    
                tool_responses.append(genai.types.Part.from_function_response(name=fc.name, response={"result": tool_result}))
                
            response = await asyncio.to_thread(chat.send_message, tool_responses)
            
        return response.text.strip()
    except Exception as exc:
        logger.error("Gemini API error: %s", exc, exc_info=True)
        return "⚠️ [Báo cáo lỗi] Hệ thống tạm thời không phản hồi. Xin thử lại sau."
