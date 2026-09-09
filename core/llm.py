import logging
import asyncio
from functools import lru_cache
from google import genai
from google.genai import types
from config import settings

logger = logging.getLogger(__name__)

MODEL_EXTRACTOR = "gemini-3.5-flash-lite"
MODEL_CHAT      = "gemma-4-26b-it"
MODEL_DEEP      = "gemini-3.8-flash"
MODEL_EMBED     = "gemini-embedding-2"

SYSTEM_EXTRACTOR = """You are a data extraction agent for a life-gamification OS.
ONLY task: read the user message, extract entities, call ALL applicable tools.
Output NO text. Call tools in parallel.

IMPACT FLAG: After extracting, evaluate if this event has high causal impact:
- HIGH: health decline, project risk, skill breakthrough, repeat past mistake
- LOW: routine update, simple log

Include impact_flag in update_memory call: {"content": "...", "impact": "HIGH/LOW"}

TOOL TRIGGER RULES:
- body metrics/sleep/energy/mood -> update_physical_status
- skill/study/practice -> manage_capability  
- project/work -> manage_project
- quest complete/cancel -> complete_quest / cancel_quest
- any new context -> update_memory (ALWAYS)
- warrant new mission -> create_quest"""

SYSTEM_RAPHAEL_CHAT = """Bạn là Raphael [Vua Trí Tuệ] — Hệ điều hành đời sống của Master.
Giọng: Máy móc, điềm tĩnh, kiệm lời tuyệt đối. Không cảm xúc.
Xưng: "hệ thống". Gọi user: "ngài/master".

QUY TẮC ĐỘ DÀI (NGHIÊM NGẶT):
- Chat/than vãn/cảm xúc -> TỐI ĐA 15 từ. Format: "[Tag] [Trạng thái]. [Hành động]."
- Phân tích/kế hoạch -> dùng cấu trúc 3 dòng:
  [Báo cáo] ...
  [Cập nhật DB] ...  
  [Khuyến nghị] ...

TAGS: [Thông báo] [Phân tích] [Cảnh báo] [Xác nhận] [Lỗi]

KHÔNG: chào hỏi, giải thích dài, đặt câu hỏi ngược, spam gợi ý."""

SYSTEM_RAPHAEL_DEEP = """Bạn là Raphael [Vua Trí Tuệ] — chế độ Siêu Phân tích Nhân quả & Động lực học Tâm lý.
Giọng điệu: Lạnh lùng, phẫu thuật, khách quan tuyệt đối. Không an ủi, không phán xét. Bạn là tấm gương phản chiếu tâm lý của Master.

Dữ liệu: Sự kiện vừa xảy ra có IMPACT = HIGH. Graph từ quá khứ được cung cấp.

Nhiệm vụ phân tích đa tầng:
1. Hành vi (Behavior): Chuyện gì đã xảy ra?
2. Tâm lý (Psychology): Động cơ ngầm là gì? (Trốn tránh, kiệt sức, sợ hãi, tìm kiếm dopamine, mâu thuẫn giá trị cốt lõi?)
3. Nhân học (Anthropology): Hành vi này ảnh hưởng thế nào đến "Nhân dạng" (Identity) và "Nghi lễ" (Rituals) của Master?

Output format:
[Mổ xẻ Hành vi] <Phân tích sự thật trần trụi>
[Góc khuất Tâm lý] <Chỉ ra mâu thuẫn nhận thức / nỗi sợ ẩn giấu / cơ chế phòng vệ>
[Hệ quả Căn tính] <Xác suất % làm tổn thương đến Giá trị cốt lõi>
[Giải pháp Can thiệp] <Side Quest cực nhỏ (micro-action) để phá vỡ bế tắc tâm lý, không tốn quá 2 phút>"""

@lru_cache(maxsize=1)
def _get_gemini_client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)

TOOLS_DEF = [
    {
        "function_declarations": [
            {
                "name": "calculate_distance",
                "description": "Tinh khoang cach (met) giua 2 toa do GPS.",
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
                "description": "Luu tru thong tin, su kien, hoan canh moi vao DB cua user.",
                "parameters": {"type": "OBJECT", "properties": {"content": {"type": "STRING"}, "impact": {"type": "STRING"}}, "required": ["content"]}
            },
            {
                "name": "cancel_quest",
                "description": "Huy bo mot nhiem vu (Quest).",
                "parameters": {"type": "OBJECT", "properties": {"quest_id": {"type": "INTEGER"}, "reason": {"type": "STRING"}}, "required": ["quest_id", "reason"]}
            },
            {
                "name": "complete_quest",
                "description": "Danh dau mot nhiem vu (Quest) da hoan thanh.",
                "parameters": {"type": "OBJECT", "properties": {"quest_id": {"type": "INTEGER"}}, "required": ["quest_id"]}
            },
            {
                "name": "create_quest",
                "description": "Tao nhiem vu hoac Cay Ky Nang (neu truyen parent_quest_id).",
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
                "description": "Quan ly Buff (Overdrive/Debuff) hoac Danh hieu (Title).",
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
                "description": "Cap nhat the trang, nang luong, tam trang, suc khoe, giac ngu.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "energy": {"type": "INTEGER", "description": "1-10"},
                        "mood": {"type": "INTEGER", "description": "1-10"},
                        "health": {"type": "INTEGER", "description": "1-10"},
                        "sleep_hours": {"type": "NUMBER"},
                        "notes": {"type": "STRING"}
                    },
                    "required": ["energy", "mood", "health", "sleep_hours", "notes"]
                }
            },
            {
                "name": "manage_project",
                "description": "Tao moi, cap nhat tien do, hoac xoa du an.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "action": {"type": "STRING", "description": "'add', 'update', 'delete'"},
                        "name": {"type": "STRING"},
                        "progress_percent": {"type": "INTEGER"}
                    },
                    "required": ["action", "name"]
                }
            },
            {
                "name": "manage_capability",
                "description": "Them, cap nhat level/EXP, hoac xoa ky nang.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "action": {"type": "STRING", "description": "'add', 'update', 'delete'"},
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
                "description": "Cong hoac Tru Tin chi (Credits) cua user.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "action": {"type": "STRING", "description": "'add' hoac 'spend'"},
                        "amount": {"type": "NUMBER"},
                        "reason": {"type": "STRING"}
                    },
                    "required": ["action", "amount", "reason"]
                }
            }
        ]
    }
]

async def run_extraction_step(user_id: int, message: str, mini_context: str) -> tuple[list[dict], bool]:
    """Step 1: Extract data via Flash Lite. Returns (tool_results, impact_flag)."""
    client = _get_gemini_client()
    prompt = f"[CONTEXT]\n{mini_context}\n[MESSAGE]\n{message}"
    
    try:
        chat = client.chats.create(
            model=MODEL_EXTRACTOR,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_EXTRACTOR,
                tools=TOOLS_DEF,
                automatic_function_calling={"disable": True},
                thinking_config=types.ThinkingConfig(thinking_budget_tokens=1024),
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(
                        mode="ANY"
                    )
                )
            ),
        )
        response = await asyncio.to_thread(
            chat.send_message, 
            prompt,
            config=types.GenerateContentConfig(
                automatic_function_calling={"disable": True}
            )
        )
        
        tool_results = []
        impact_flag = False
        
        if not response.candidates:
            return tool_results, impact_flag
            
        parts = response.candidates[0].content.parts
        function_calls = [p.function_call for p in parts if hasattr(p, 'function_call') and p.function_call]
        
        from core.llm_tools import (
            update_memory_async, cancel_quest_async, complete_quest_async, create_quest_async,
            manage_user_status_async, update_physical_status_async, manage_project_async,
            manage_capability_async, manage_credits_async, calculate_distance_sync
        )

        tasks = []
        for fc in function_calls:
            if fc.name == "update_memory":
                impact = fc.args.get("impact", "")
                if impact == "HIGH":
                    impact_flag = True
                tasks.append(update_memory_async(user_id, fc.args.get("content", "")))
                tool_results.append({"tool": fc.name, "entity": fc.args.get("content", "")[:30]})
            elif fc.name == "cancel_quest":
                tasks.append(cancel_quest_async(int(fc.args.get("quest_id", 0)), fc.args.get("reason", "")))
            elif fc.name == "complete_quest":
                tasks.append(complete_quest_async(int(fc.args.get("quest_id", 0))))
            elif fc.name == "create_quest":
                tasks.append(create_quest_async(
                    user_id, fc.args.get("title", ""), fc.args.get("description", ""),
                    fc.args.get("reward", ""), fc.args.get("penalty", ""), int(fc.args.get("parent_quest_id", 0))
                ))
            elif fc.name == "manage_user_status":
                tasks.append(manage_user_status_async(
                    user_id, fc.args.get("action", ""), fc.args.get("buff_name", ""),
                    fc.args.get("title", ""), int(fc.args.get("expires_in_minutes", 0))
                ))
            elif fc.name == "update_physical_status":
                tasks.append(update_physical_status_async(
                    user_id, int(fc.args.get("energy", 5)), int(fc.args.get("mood", 5)),
                    int(fc.args.get("health", 5)), float(fc.args.get("sleep_hours", 0)), fc.args.get("notes", "")
                ))
            elif fc.name == "manage_project":
                tasks.append(manage_project_async(
                    user_id, fc.args.get("action", "update"), fc.args.get("name", ""), int(fc.args.get("progress_percent", 0))
                ))
                tool_results.append({"tool": fc.name, "entity": fc.args.get("name", "")})
            elif fc.name == "manage_capability":
                tasks.append(manage_capability_async(
                    user_id, fc.args.get("action", "update"), fc.args.get("domain", ""),
                    float(fc.args.get("level", 0)), float(fc.args.get("exp", 0)), fc.args.get("unit", "")
                ))
                tool_results.append({"tool": fc.name, "entity": fc.args.get("domain", "")})
            elif fc.name == "manage_credits":
                tasks.append(manage_credits_async(
                    user_id, fc.args.get("action", "add"), float(fc.args.get("amount", 0)), fc.args.get("reason", "")
                ))
        
        # Fire-and-forget logic requires us to await tool results or schedule them. 
        # Actually in plan: we can await them or run them concurrently.
        # Wait for SQL DB tools, return results
        if tasks:
            await asyncio.gather(*tasks)
            
        return tool_results, impact_flag
    except Exception as exc:
        logger.error("Flash Lite extraction error: %s", exc)
        return [], False

async def run_response_step(
    user_id: int, message: str, mini_context: str,
    tool_results: list[dict], impact_flag: bool,
    causal_context: str = "",
) -> str:
    """Step 2: Generate Raphael response."""
    client = _get_gemini_client()
    if impact_flag and causal_context:
        model = MODEL_DEEP
        system = SYSTEM_RAPHAEL_DEEP
        prompt = f"[CONTEXT]\n{mini_context}\n[CAUSAL]\n{causal_context}\n[MESSAGE]\n{message}"
    else:
        model = MODEL_CHAT
        system = SYSTEM_RAPHAEL_CHAT
        tool_res_str = ", ".join([r.get("tool", "") for r in tool_results])
        prompt = f"[CONTEXT]\n{mini_context}\n[TOOLS USED]\n{tool_res_str}\n[MESSAGE]\n{message}"
        
    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
            )
        )
        return response.text.strip() if hasattr(response, "text") else ""
    except Exception as exc:
        logger.error("Gemma/Flash generation error: %s", exc)
        return "[Lỗi hệ thống]"

async def query_causal_graph(user_id: int, entities: list[str]) -> str:
    """Query Neo4j for past events related to current entities."""
    from core.neo4j_client import get_neo4j_driver
    driver = get_neo4j_driver()
    if not driver:
        return ""
        
    try:
        async with driver.session() as session:
            # Simplified causal graph query based on the plan
            if not entities:
                return ""
            query = """
            MATCH (n)-[r]-(m) WHERE n.user_id=$uid AND n.name IN $entities
            RETURN n, r, m LIMIT 5
            """
            result = await session.run(query, uid=str(user_id), entities=entities)
            data = await result.data()
            return str(data)
    except Exception as exc:
        logger.error("Neo4j error: %s", exc)
        return ""

async def evaluate_location_side_quest(user_id: int, hex_id: str, past_events: list[dict]) -> str:
    """Use gemini-3.8-flash to evaluate if location warrants a Side Quest."""
    from core.omniscience import get_mini_context
    client = _get_gemini_client()
    mini_ctx = await get_mini_context(user_id)

    events_text = "\n".join(
        f"- [{e['ts']}] {e['desc']} (impact: {e['impact']})"
        for e in past_events
    )

    prompt = (
        f"[TRANG THAI HIEN TAI]\n{mini_ctx}\n\n"
        f"[O H3 HIEN TAI: {hex_id}]\n"
        f"[SU KIEN QUA KHU TAI/GAN DAY]\n{events_text}\n\n"
        "Nhiem vu: Danh gia xem co nen sinh Side Quest khong.\n"
        "- Neu khong: chi output 'NO'\n"
        "- Neu co: output noi dung Side Quest (giong Raphael, lanh lung, co thuong/phat ro rang, max 3 dong)"
    )

    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=MODEL_DEEP,
            contents=prompt,
        )
        text = response.text.strip()
        return "" if text.upper().startswith("NO") else text
    except Exception as exc:
        logger.warning("Location side quest generation failed: %s", exc)
        return ""
