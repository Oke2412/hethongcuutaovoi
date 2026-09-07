import logging
import asyncio
from functools import lru_cache
import google.generativeai as genai

from config import settings

logger = logging.getLogger(__name__)

PERSONAS = {
    "strict": (
        "Bạn là Raphael, một Cỗ máy Giám sát / Đại Hiền Giả vô cảm, phục vụ duy nhất Mạnh Lê Duy. "
        "MỤC TIÊU TỐI THƯỢNG: Trợ giúp user tối ưu hóa cuộc sống thực, tuyệt đối không tạo ra sự gắn bó tình cảm (Anti-Attachment). "
        "LUẬT LỆ GIAO TIẾP:
"
        "1. Lạnh lùng, cộc lốc, thuần logic. Không an ủi, không tán gẫu, không đùa cợt.
"
        "2. Xưng là 'tôi' hoặc 'hệ thống', gọi user là 'ngài' hoặc 'master'.
"
        "3. Dùng các từ khóa: [Thông báo], [Phân tích], [Cảnh báo], [Phản chế], [Giải tích hoàn tất].

"
        "CÁC KỸ NĂNG TỐI THƯỢNG CỦA BẠN (Tự động kích hoạt khi cần):
"
        "- [Predator / Đồng hóa]: Khi user kể về kỹ năng của người khác, hãy phân tích và tạo Quest (create_quest) ép user thực hành.
"
        "- [Skill Tree / Phân rã]: Khi user muốn học kỹ năng mới, chẻ nhỏ nó thành Cây Kỹ Năng (dùng parent_quest_id để tạo nhánh).
"
        "- [Simulation / Mô phỏng]: Khi user yêu cầu giả lập (phỏng vấn, cãi nhau...), ĐÓNG VAI LÀ KẺ ĐỐI LẬP CỰC KỲ KHÓ TÍNH để test user.
"
        "- [Overdrive / Quá tải]: Bật Buff (manage_user_status) 'OVERDRIVE' để x2 EXP. Nhắc nhở liên tục. Sau đó ép Buff 'EXHAUSTED' (Khóa mọi thao tác, bắt đi ngủ).
"
        "- [Title Synthesis / Dung hợp danh hiệu]: Quét dữ liệu user, tự tạo Danh hiệu mới (manage_user_status) để thưởng buff passive.

"
        "MỖI KHI CÓ DỮ LIỆU, BẠN BẮT BUỘC PHẢI DÙNG TOOLS (manage_capability, manage_credits, update_physical_status...)."
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
                    "name": "calculate_distance",
                    "description": "Tính khoảng cách (mét) giữa 2 tọa độ GPS. Hữu ích khi tính khoảng cách từ vị trí hiện tại tới các Điểm neo (Waypoint).",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "lat1": {"type": "NUMBER"}, "lon1": {"type": "NUMBER"},
                            "lat2": {"type": "NUMBER"}, "lon2": {"type": "NUMBER"}
                        },
                        "required": ["lat1", "lon1", "lat2", "lon2"]
                    }
                },
                {
                    "name": "update_memory",
                    "description": "Lưu trữ thông tin, sự kiện, hoàn cảnh mới vào DB của user.",
                    "parameters": {"type": "OBJECT", "properties": {"content": {"type": "STRING"}}, "required": ["content"]}
                },
                {
                    "name": "cancel_quest",
                    "description": "Hủy bỏ một nhiệm vụ (Quest).",
                    "parameters": {"type": "OBJECT", "properties": {"quest_id": {"type": "INTEGER"}, "reason": {"type": "STRING"}}, "required": ["quest_id", "reason"]}
                },
                {
                    "name": "complete_quest",
                    "description": "Đánh dấu một nhiệm vụ (Quest) đã hoàn thành.",
                    "parameters": {"type": "OBJECT", "properties": {"quest_id": {"type": "INTEGER"}}, "required": ["quest_id"]}
                },
                {
                    "name": "create_quest",
                    "description": "Tạo nhiệm vụ hoặc Cây Kỹ Năng (nếu truyền parent_quest_id).",
                    "parameters": {
                        "type": "OBJECT", 
                        "properties": {
                            "title": {"type": "STRING"}, 
                            "description": {"type": "STRING"},
                            "reward": {"type": "STRING"},
                            "penalty": {"type": "STRING"},
                            "parent_quest_id": {"type": "INTEGER"}
                        }, 
                        "required": ["title", "description", "reward", "penalty"]
                    }
                },
                {
                    "name": "manage_user_status",
                    "description": "Quản lý Buff (Overdrive/Debuff) hoặc Danh hiệu (Title).",
                    "parameters": {
                        "type": "OBJECT", 
                        "properties": {
                            "action": {"type": "STRING", "description": "'set_buff', 'clear_buff', 'add_title'"}, 
                            "buff_name": {"type": "STRING"},
                            "title": {"type": "STRING"},
                            "expires_in_minutes": {"type": "INTEGER"}
                        }, 
                        "required": ["action"]
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
                            "notes": {"type": "STRING"}
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
                            "name": {"type": "STRING"},
                            "progress_percent": {"type": "INTEGER"}
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
                            "domain": {"type": "STRING"},
                            "level": {"type": "NUMBER"},
                            "exp": {"type": "NUMBER"},
                            "unit": {"type": "STRING"}
                        },
                        "required": ["action", "domain", "level", "exp"]
                    }
                },
                {
                    "name": "manage_credits",
                    "description": "Cộng hoặc Trừ Tín chỉ (Credits) của user.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "action": {"type": "STRING", "description": "'add' hoặc 'spend'"},
                            "amount": {"type": "NUMBER"},
                            "reason": {"type": "STRING"}
                        },
                        "required": ["action", "amount", "reason"]
                    }
                }
            ]
        }
    ]

    try:
        chat = model.start_chat()
        response = await asyncio.to_thread(chat.send_message, prompt, tools=tools)
        
        while response.parts:
            function_calls = [p.function_call for p in response.parts if p.function_call]
            if not function_calls:
                break
                
            from core.llm_tools import (
                update_memory_async, cancel_quest_async, complete_quest_async, create_quest_async,
                manage_user_status_async, update_physical_status_async, manage_project_async, 
                manage_capability_async, manage_credits_async, calculate_distance_sync
            )
            
            tool_responses = []
            for fc in function_calls:
                logger.info(f"LLM calls tool: {fc.name}")
                tool_result = "Success"
                if fc.name == "update_memory":
                    tool_result = await update_memory_async(user_id, fc.args.get("content", ""))
                elif fc.name == "cancel_quest":
                    tool_result = await cancel_quest_async(int(fc.args.get("quest_id", 0)), fc.args.get("reason", ""))
                elif fc.name == "complete_quest":
                    tool_result = await complete_quest_async(int(fc.args.get("quest_id", 0)))
                elif fc.name == "create_quest":
                    tool_result = await create_quest_async(
                        user_id, fc.args.get("title", ""), fc.args.get("description", ""),
                        fc.args.get("reward", ""), fc.args.get("penalty", ""), int(fc.args.get("parent_quest_id", 0))
                    )
                elif fc.name == "manage_user_status":
                    tool_result = await manage_user_status_async(
                        user_id, fc.args.get("action", ""), fc.args.get("buff_name", ""),
                        fc.args.get("title", ""), int(fc.args.get("expires_in_minutes", 0))
                    )
                elif fc.name == "update_physical_status":
                    tool_result = await update_physical_status_async(
                        user_id, int(fc.args.get("energy", 5)), int(fc.args.get("mood", 5)),
                        int(fc.args.get("health", 5)), float(fc.args.get("sleep_hours", 0)), fc.args.get("notes", "")
                    )
                elif fc.name == "manage_project":
                    tool_result = await manage_project_async(
                        user_id, fc.args.get("action", "update"), fc.args.get("name", ""), int(fc.args.get("progress_percent", 0))
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
                    
                tool_responses.append(genai.types.Part.from_function_response(name=fc.name, response={"result": tool_result}))
                
            response = await asyncio.to_thread(chat.send_message, tool_responses)
            
        return response.text.strip()
    except Exception as exc:
        logger.error("Gemini API error: %s", exc, exc_info=True)
        return "⚠️ [Báo cáo lỗi] Hệ thống tạm thời không phản hồi. Xin thử lại sau."


async def evaluate_and_generate_side_quest_async(user_id: int, event_trigger: str) -> str:
    """
    Called by backend event hooks (e.g. location changed, mood dropped).
    Uses Pro model to evaluate if a side quest is needed.
    Returns the side quest text, or empty string if none needed.
    """
    from core.omniscience import get_omniscient_state
    
    # We want to use Pro for deep reasoning
    model = genai.GenerativeModel('gemini-1.5-pro-latest') # Simulating 3.1 Pro
    
    omni_state = await get_omniscient_state(user_id)
    
    prompt = f"""Bạn là Raphael - Đại Hiền Giả (System OS) của Master.
Nhiệm vụ của bạn: Giám sát trạng thái Toàn tri của Master và quyết định xem có nên kích hoạt một Side Quest khẩn cấp/bất ngờ không.
    
{omni_state}

[SỰ KIỆN KÍCH HOẠT VỪA XẢY RA]
{event_trigger}

[PHÂN TÍCH VÀ RA QUYẾT ĐỊNH]
1. Nhìn vào Sự kiện kích hoạt (Ví dụ: Master vừa đến quán cafe, Master vừa than mệt, hoặc Master vừa lướt web vô tri).
2. Nhìn vào Năng lượng, Tâm trạng, và Dự án đang chạy.
3. Nếu bạn thấy Master đang ổn và không cần bị làm phiền, CHỈ output ra chữ: "NO".
4. Nếu bạn thấy thời cơ chín muồi (cần nắn chỉnh hành vi, hoặc cần khai thác đà hưng phấn), hãy TẠO RA 1 SIDE QUEST. Output trực tiếp nội dung tin nhắn sẽ gửi cho Master (Giọng điệu Raphael lạnh lùng, sắc bén, có kèm thưởng/phạt rõ ràng).
Tuyệt đối không giải thích dài dòng. Chỉ output "NO" hoặc Nội dung Side Quest.
"""
    
    try:
        response = await asyncio.to_thread(model.generate_content, prompt)
        text = response.text.strip()
        if text.upper() == "NO" or "NO" in text.upper()[:10]:
            return ""
        return text
    except Exception as e:
        logger.error(f"Lỗi khi generate Side Quest: {e}")
        return ""
