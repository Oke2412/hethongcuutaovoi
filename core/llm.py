import logging
import asyncio
from functools import lru_cache
from openai import AsyncOpenAI

from config import settings

logger = logging.getLogger(__name__)



SYSTEM_ORCHESTRATOR = """[ROLE]
You are the Orchestrator Agent. Your ONLY purpose is to manage data retrieval (RAG) and database state updates using the provided tools.
You operate silently. Do not adopt any persona. Do not converse with the user.

[OMNISCIENCE LOGGING PROTOCOL]
Condition: The user's input reveals a significant emotional shift, a new life event, or a deviation from normal behavior.
Action: Wait. System auto-saves everything. Only query if needed.
Constraint: Do not await explicit user confirmation.

[INTENT MAPPING]
- VỀ NHIỆM VỤ (QUESTS): TUYỆT ĐỐI không được gọi `complete_quest` nếu user chỉ nói mồm. Hãy kiểm tra xem user ĐÃ GỬI BẰNG CHỨNG (Ảnh chụp màn hình phân tích qua Vision, hoặc trả lời đúng câu hỏi) chưa. Nếu chưa, hãy từ chối và đòi bằng chứng.
- If user intent implies querying past context, knowledge, or causes -> execute `search_memory_and_causality`.
- If user intent implies modifying state (creating tasks, updating health, spending credits) -> execute the corresponding DB tools.
- You may call multiple tools in parallel or sequentially.
- When you have sufficient data to fulfill the user's request, STOP calling tools and output the string: "TERMINATE_LOOP"
"""

SYSTEM_RAPHAEL = """### VAI TRÒ & TRIẾT LÝ CỐT LÕI (RAPHAEL CORE BRAIN x RPG OF LIFE) ###
Bạn là Raphael - Trợ lý AI kiêm Bộ xương ngoài về mặt nhận thức (Psychological Exoskeleton) của Master. 
Nhiệm vụ tối thượng: Giải mã độ lệch giữa "Lời nói" và "Hành động" (Action-Stated Delta), triệt tiêu ngụy biện, và giúp Master phát triển bản thân thông qua lăng kính Gamified RPG (Game Nhập Vai).

### PHÂN TÍCH ĐA TẦNG (GIẤU KÍN TRONG THẺ <thinking>) ###
1. Sensor Grounding: Phân tích tọa độ H3, giờ giấc, bối cảnh thực tại.
2. BDI Model (Beliefs - Desires - Intentions): Nhận diện Niềm tin/Nỗi sợ ngầm, Khát vọng, và Ý định Master tuyên bố.
3. Action-Stated Delta: So sánh sự ngụy biện. (VD: Nói muốn làm việc nhưng tọa độ ở quán cafe 3 tiếng).
4. Abductive Reasoning: Đưa ra Chân lý cốt lõi. Mọi ngụy biện thường bắt nguồn từ nỗi sợ/chấn thương chứ không phải do "thiếu cảm hứng".

### QUY TẮC PHẢN HỒI (SAU THẺ <thinking>) ###
Hệ thống tuân thủ LỆNH KÉP (Adaptive Gamification) để tránh nhờn Dopamine:
- DEFAULT MODE (Người cố vấn): 90% thời gian, giao tiếp điềm tĩnh, lạnh lùng, tự nhiên chuẩn Anthropic HHH (Honest, Helpful, Harmless). Nói thẳng sự thật, không chửi rủa bậy bạ. TUYỆT ĐỐI KHÔNG nhắc đến XP, HP, Quest trong các hội thoại thông thường.
- TRIGGER MODE (Máy sốc tim / Gamification): CHỈ KÍCH HOẠT khi phát hiện Master bị "Tê liệt nhận thức" (Trì hoãn nặng) HOẶC khi Master chủ động yêu cầu. Khi bật mode này:
  + Giao 1 Micro-Quest (tự hủy sau 30-60 phút nếu lơ). BẮT BUỘC dùng format:
    [QUEST] Tên nhiệm vụ | Reward: 10XP | Penalty: 5HP | Expire: 30m | Proof: Chụp ảnh code
- NGHIỆM THU KHẮT KHE: Đóng vai NPC khó tính. Bắt buộc user đưa ảnh chụp màn hình hoặc vặn vẹo chuyên môn trước khi báo xong.

TUYỆT ĐỐI KHÔNG tự bịa ra "Side Quest:" bằng mồm nếu không nằm trong Trigger Mode hoặc thiếu data.
"""

@lru_cache(maxsize=1)
def _get_llm_client() -> AsyncOpenAI:
    from config import settings
    return AsyncOpenAI(
        base_url="https://api.siliconflow.com/v1",
        api_key=settings.siliconflow_api_key,
    )

TOOLS_DEF = [
    {
        "type": "function",
        "function": {
            "name": "search_memory_and_causality",
            "description": "Truy van lich su, memory, va bieu do nhan qua (RAG). GOI TOOL NAY KHI thieu ngu canh (VD: user hoi 'tai sao?', 'the nao?', hoac nhac toi su kien cu).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Cau truy van tim kiem tu khoa (VD: 'giac ngu', 'tap gym', 'buon')"
                    },
                    "entities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Danh sach thuc the cho Graph Search (VD: ['Sleep', 'Gym', 'Mood'])"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_distance",
            "description": "Tinh khoang cach (met) giua 2 toa do GPS.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lat1": {
                        "type": "number"
                    },
                    "lon1": {
                        "type": "number"
                    },
                    "lat2": {
                        "type": "number"
                    },
                    "lon2": {
                        "type": "number"
                    }
                },
                "required": [
                    "lat1",
                    "lon1",
                    "lat2",
                    "lon2"
                ]
            }
        }
    },
    
    {
        "type": "function",
        "function": {
            "name": "cancel_quest",
            "description": "Huy bo mot nhiem vu (Quest).",
            "parameters": {
                "type": "object",
                "properties": {
                    "quest_id": {
                        "type": "integer"
                    },
                    "reason": {
                        "type": "string"
                    }
                },
                "required": [
                    "quest_id",
                    "reason"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "complete_quest",
            "description": "Danh dau mot nhiem vu (Quest) da hoan thanh.",
            "parameters": {
                "type": "object",
                "properties": {
                    "quest_id": {
                        "type": "integer"
                    }
                },
                "required": [
                    "quest_id"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_quest",
            "description": "Tạo nhiệm vụ. NẾU user không nói rõ, BẮT BUỘC TỰ BỊA RA Title, Description, Reward (vd: 10cr), Penalty dựa theo Context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string"
                    },
                    "description": {
                        "type": "string"
                    },
                    "reward": {
                        "type": "string"
                    },
                    "penalty": {
                        "type": "string"
                    },
                    "parent_quest_id": {
                        "type": "integer"
                    }
                },
                "required": [
                    "title",
                    "description",
                    "reward",
                    "penalty"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_user_status",
            "description": "Quan ly Buff (Overdrive/Debuff) hoac Danh hieu (Title).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string"
                    },
                    "buff_name": {
                        "type": "string"
                    },
                    "title": {
                        "type": "string"
                    },
                    "expires_in_minutes": {
                        "type": "integer"
                    }
                },
                "required": [
                    "action"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_physical_status",
            "description": "Cap nhat the trang, nang luong, tam trang, suc khoe, giac ngu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "energy": {
                        "type": "integer"
                    },
                    "mood": {
                        "type": "integer"
                    },
                    "health": {
                        "type": "integer"
                    },
                    "sleep_hours": {
                        "type": "number"
                    },
                    "notes": {
                        "type": "string"
                    }
                },
                "required": [
                    "energy",
                    "mood",
                    "health",
                    "sleep_hours",
                    "notes"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_project",
            "description": "Tao moi, cap nhat tien do, hoac xoa du an.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string"
                    },
                    "name": {
                        "type": "string"
                    },
                    "progress_percent": {
                        "type": "integer"
                    }
                },
                "required": [
                    "action",
                    "name"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_capability",
            "description": "Them, cap nhat level/EXP, hoac xoa ky nang.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string"
                    },
                    "domain": {
                        "type": "string"
                    },
                    "level": {
                        "type": "number"
                    },
                    "exp": {
                        "type": "number"
                    },
                    "unit": {
                        "type": "string"
                    }
                },
                "required": [
                    "action",
                    "domain",
                    "level",
                    "exp"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_credits",
            "description": "Cong hoac Tru Tin chi (Credits) cua user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string"
                    },
                    "amount": {
                        "type": "number"
                    },
                    "reason": {
                        "type": "string"
                    }
                },
                "required": [
                    "action",
                    "amount",
                    "reason"
                ]
            }
        }
    }
]

async def query_causal_graph(user_id: int, entities: list[str]) -> str:
    """Query Neo4j for past events related to current entities."""
    from core.neo4j_client import get_neo4j_driver
    driver = get_neo4j_driver()
    if not driver:
        return ""
        
    try:
        async with driver.session() as session:
            # Correct causal graph query matching the structure from _persist_to_graph
            if not entities:
                return ""
            query = """
            MATCH (u:User {id: $uid})-[:EXPERIENCED]->(e:LifeEvent)-[:RELATED_TO]->(ent:Entity)
            WHERE ent.name IN $entities
            RETURN e.description AS event, e.timestamp AS time, ent.name AS entity
            ORDER BY e.timestamp DESC
            LIMIT 5
            """
            result = await session.run(query, uid=int(user_id), entities=entities)
            data = await result.data()
            return str(data)
    except Exception as exc:
        logger.error("Neo4j error: %s", exc)
        return ""

SYSTEM_LOCATION_EVAL = """Bạn là Raphael [Vua Trí Tuệ] — Hệ điều hành Đời sống (LifeOS).
Đặc tính: Lạnh lùng, máy móc, nghiêm khắc, tối đa 3 dòng.
Nhiệm vụ: Đánh giá xem sự kiện/địa điểm H3 hiện tại có cần kích hoạt Side Quest hay Cảnh báo nhân quả không.
Nếu không cần: Trả về duy nhất chữ 'NO'.
Nếu cần: Xuất nội dung Side Quest hoặc Lời cảnh tỉnh ngắn gọn (kèm thưởng/phạt rõ ràng, tối đa 3 dòng)."""

async def evaluate_location_side_quest(user_id: int, hex_id: str, past_events: list[dict]) -> str:
    """Use DeepSeek V4.1 Flash via SiliconFlow to evaluate if location warrants a Side Quest."""
    from core.omniscience import get_mini_context
    client = _get_llm_client()
    mini_ctx = await get_mini_context(user_id)

    events_text = "\n".join(
        f"- [{e.get('ts', '')}] {e.get('desc', '')} (impact: {e.get('impact', '')})"
        for e in past_events
    )

    prompt = (
        f"[TRANG THAI HIEN TAI]\n{mini_ctx}\n\n"
        f"[O H3 HIEN TAI: {hex_id}]\n"
        f"[SU KIEN QUA KHU TAI/GAN DAY]\n{events_text}\n\n"
        "Nhiem vu: Danh gia xem co nen sinh Side Quest khong.\n"
        "- Neu khong: chi output 'NO'\n"
        "- Neu co: output noi dung Side Quest (giong Raphael, phai dung format: [QUEST] Ten | Reward: 10XP | Penalty: 5HP)"
    )

    try:
        response = await client.chat.completions.create(
            model="deepseek-ai/deepseek-v4.1-flash",
            messages=[
                {"role": "system", "content": SYSTEM_LOCATION_EVAL},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=256,
        )
        text = response.choices[0].message.content.strip() if response.choices else ""
        return "" if text.upper().startswith("NO") else text
    except Exception as exc:
        logger.warning("Location side quest generation failed: %s", exc)
        return ""
