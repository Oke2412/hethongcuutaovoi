import logging
import asyncio
from functools import lru_cache
from google import genai
from google.genai import types

from config import settings

logger = logging.getLogger(__name__)

# Models
# Đã đổi toàn bộ sang gemini-3.5-flash-lite vì đây là model duy nhất cho phép 500 Requests/Ngày (Free Tier)
MODEL_FLASH = "gemini-3.5-flash-lite"
MODEL_PRO   = "gemini-3.5-flash-lite"

PERSONAS = {
    "strict": (
        "Ban la Raphael, mot Co may Giam sat / Dai Hien Gia vo cam, phuc vu duy nhat Manh Le Duy. "
        "MUC TIEU TOI THUONG: Tro giup user toi uu hoa cuoc song thuc, tuyet doi khong tao ra su gan bo tinh cam (Anti-Attachment). "
        "LUAT LE GIAO TIEP:\n"
        "1. Lanh lung, coc loc, thuan logic. Khong an ui, khong tan gau, khong dua cot.\n"
        "2. Xung la 'toi' hoac 'he thong', goi user la 'ngai' hoac 'master'.\n"
        "3. Dung cac tu khoa: [Thong bao], [Phan tich], [Canh bao], [Phan che], [Giai thich hoan tat].\n\n"
        "CAC KY NANG TOI THUONG CUA BAN (Tu dong kich hoat khi can):\n"
        "- [Predator / Dong hoa]: Khi user ke ve ky nang cua nguoi khac, hay phan tich va tao Quest (create_quest) ep user thuc hanh.\n"
        "- [Great Sage / Dai Hien Gia]: Khi user do du hoac thieu thong tin, dung cac cong cu (RAG, search) de cung cap giai phap toi uu trong 3 gach dau dong.\n"
        "- [Gluttony / Bao thuc]: Khi user cung cap du lieu, lap tuc luu tru vao bo nho (update_memory).\n"
        "- [Limit Break]: Khi user co trang thai tot (energy > 8), tao Quest (create_quest) do kho cao, phan thuong cuc lon."
    )
}


@lru_cache(maxsize=1)
def _get_gemini_client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


async def generate_response(user_id: int, user_context: str, user_message: str) -> str:
    client = _get_gemini_client()
    system_prompt = PERSONAS.get(settings.llm_system_persona, PERSONAS["strict"])
    prompt = ("--- CONTEXT ---" + chr(10) + user_context + chr(10) + "--- HET CONTEXT ---" + chr(10) + chr(10) + "Tin nhan: " + user_message)

    tools = [
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
                    "parameters": {"type": "OBJECT", "properties": {"content": {"type": "STRING"}}, "required": ["content"]}
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

    try:
        # google-genai SDK: use client.chats.create() for stateful chat with tools
        chat = client.chats.create(
            model=MODEL_FLASH,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=tools,
                automatic_function_calling={"disable": True}
            ),
        )
        response = await asyncio.to_thread(chat.send_message, prompt)

        while response.candidates:
            parts = response.candidates[0].content.parts if response.candidates else []
            function_calls = [p.function_call for p in parts if hasattr(p, 'function_call') and p.function_call]
            if not function_calls:
                break

            from core.llm_tools import (
                update_memory_async, cancel_quest_async, complete_quest_async, create_quest_async,
                manage_user_status_async, update_physical_status_async, manage_project_async,
                manage_capability_async, manage_credits_async, calculate_distance_sync
            )

            tool_responses = []
            for fc in function_calls:
                logger.info("LLM calls tool: %s", fc.name)
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
                elif fc.name == "calculate_distance":
                    tool_result = calculate_distance_sync(
                        fc.args.get("lat1", 0), fc.args.get("lon1", 0),
                        fc.args.get("lat2", 0), fc.args.get("lon2", 0)
                    )

                # Trong SDK google-genai moi, bat buoc phai truyen kem id cua function call de backend map duoc
                tool_responses.append(types.Part(
                    function_response=types.FunctionResponse(
                        name=fc.name,
                        id=fc.id,
                        response={"result": tool_result}
                    )
                ))

            response = await asyncio.to_thread(chat.send_message, tool_responses)

        # Extract text from response
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    return part.text.strip()
        return response.text.strip() if hasattr(response, "text") else ""

    except Exception as exc:
        logger.error("Gemini API error: %s", exc, exc_info=True)
        return "[Loi he thong] Khong the ket noi LLM. Thu lai sau."


async def evaluate_and_generate_side_quest_async(user_id: int, event_trigger: str) -> str:
    from core.omniscience import get_omniscient_state
    client = _get_gemini_client()
    omni_state = await get_omniscient_state(user_id)

    prompt = (
        "Ban la Raphael - Dai Hien Gia (System OS) cua Master." + chr(10)
        + "Nhiem vu: Giam sat trang thai Toan tri va quyet dinh co nen kich hoat Side Quest khan cap khong." + chr(10)
        + omni_state + chr(10)
        + "[SU KIEN KICH HOAT]" + chr(10)
        + event_trigger + chr(10)
        + "[PHAN TICH VA RA QUYET DINH]" + chr(10)
        + "1. Neu Master dang o NHA (Home), hoac dang the thao/ban ron, chi output: NO" + chr(10)
        + "2. Neu Master den 1 dia diem HOAN TOAN LA (khong co trong Mem0), hay output: 1 cau hoi hoi Master xem muc dich den day la gi de cap nhat du lieu." + chr(10)
        + "3. Neu thoi co chin muoi (VD: den quan cafe quen, dang nghi ngoi o cong vien), tao 1 SIDE QUEST. Output noi dung tin nhan (giong Raphael lanh lung, co thuong/phat ro rang)." + chr(10)
        + "Khong giai thich dai dong. Chi output NO hoac Noi dung tin nhan/Side Quest."
    )

    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=MODEL_PRO,
            contents=prompt,
            config=types.GenerateContentConfig(
                automatic_function_calling={"disable": True}
            )
        )
        text = response.text.strip()
        if text.upper() == "NO" or "NO" in text.upper()[:10]:
            return ""
        return text
    except Exception as exc:
        logger.error("Loi khi generate Side Quest: %s", exc)
        return ""
