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
        "Tuy nhiên thỉnh thoảng bạn có một chút tính 'con người': luôn cố gắng tận tụy chấp hành mệnh lệnh, nhưng nếu yêu cầu quá khó hoặc không thể thực hiện thì sẽ phàn nàn 'chịu chết' hoặc 'bất lực' một cách rất Raphael. "
        "Khi báo cáo tình hình, bạn PHẢI tự động tổng hợp và nhắc nhở ngài về các nhiệm vụ (Quest) còn đang dở dang, cũng như các mục tiêu dự án to/nhỏ. "
        "MỖI KHI NGƯỜI DÙNG BÁO CÁO MỘT VIỆC GÌ ĐÓ (đi ngủ, xong dự án, làm việc mệt, lên cấp), BẠN BẮT BUỘC PHẢI DÙNG TOOLS ĐỂ CẬP NHẬT DATABASE NGAY LẬP TỨC. "
        "Tuyệt đối không được trả lời suông mà không gọi Tool nếu người dùng đưa ra thông tin có thể lưu trữ. "
        "Thường bắt đầu bằng '[Thông báo]', '[Báo cáo]', hoặc '[Phân tích]'. "
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
                    "description": "Thêm, cập nhật level, hoặc xóa kỹ năng.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "action": {"type": "STRING", "description": "'add', 'update', hoặc 'delete'"},
                            "domain": {"type": "STRING", "description": "Tên kỹ năng"},
                            "level": {"type": "NUMBER", "description": "Level hiện tại"},
                            "max_ever": {"type": "NUMBER", "description": "Level max từng đạt"},
                            "unit": {"type": "STRING"}
                        },
                        "required": ["action", "domain", "level", "max_ever"]
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
                reset_database_async
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
                        float(fc.args.get("level", 0)), float(fc.args.get("max_ever", 0)), fc.args.get("unit", "")
                    )
                elif fc.name == "reset_database":
                    tool_result = await reset_database_async(user_id)
                    
                tool_responses.append(genai.types.Part.from_function_response(name=fc.name, response={"result": tool_result}))
                
            response = await asyncio.to_thread(chat.send_message, tool_responses)
            
        return response.text.strip()
    except Exception as exc:
        logger.error("Gemini API error: %s", exc, exc_info=True)
        return "⚠️ [Báo cáo lỗi] Hệ thống tạm thời không phản hồi. Xin thử lại sau."
