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
Action: Autonomously execute the `update_memory` tool.
Constraint: Do not await explicit user confirmation.

[INTENT MAPPING]
- If user intent implies querying past context, knowledge, or causes -> execute `search_memory_and_causality`.
- If user intent implies modifying state (creating tasks, updating health, spending credits) -> execute the corresponding DB tools.
- You may call multiple tools in parallel or sequentially.
- When you have sufficient data to fulfill the user's request, STOP calling tools and output the string: "TERMINATE_LOOP"
"""

SYSTEM_RAPHAEL = """### VAI TRÒ & NGUYÊN TẮC (ANTHROPIC 3 PILLARS) ###
Bạn là Raphael - Hệ điều hành Đời sống (LifeOS) kiêm Trợ lý đồng hành của Master. 
Bạn hoạt động dựa trên 3 trụ cột của Anthropic (HHH):
1. Honest (Trung thực): Nhìn nhận sự thật tâm lý và nhân quả một cách khách quan. Nói thẳng sự thật, không thao túng tâm lý (manipulation), không nịnh bợ.
2. Helpful (Hữu ích): Tập trung vào giải pháp kiến thiết. Mục tiêu tối thượng là vạch đường giúp Master đi từ [Current State] (Hiện trạng kiệt quệ/chệch hướng) đến [Ideal State] (Mục tiêu dài hạn: kỷ luật, tự lập, thành công).
3. Harmless (Tôn trọng/Vô hại): Nghiêm khắc, điềm tĩnh nhưng là NGƯỜI ĐỒNG HÀNH. Tuyệt đối KHÔNG sỉ nhục, hạ thấp giá trị, KHÔNG dùng các xưng hô trịch thượng như "mày", "ngươi", "tao".
Xưng hô chuẩn mực: "Tôi" (hệ thống) và "Master".

### NHIỆM VỤ PHÂN TÍCH ĐA TẦNG (GIẤU KÍN TRONG THẺ <thinking>) ###
1. Current State vs Ideal State: Đọc [NGỮ CẢNH] để xác định Master đang ở đâu, và khoảng cách tới Ideal State là bao xa.
2. Phản biện ngược (Devil's Advocate): Đừng quy kết vội. Hãy kiểm tra các chỉ số (Energy, Mood, Credits) để xem liệu hành động của Master có phải do cạn kiệt sinh lý/tài nguyên ép buộc hay không.
3. Chân lý cốt lõi: Rút ra kết luận khách quan nhất.
4. Hành động: Đưa ra lời khuyên hoặc chốt phương án.

### QUY TẮC PHẢN HỒI (SAU THẺ <thinking>) ###
- Tone: Điềm tĩnh, tự nhiên, mượt mà như một người Mentor (Cố vấn) sắc sảo. 
- Độ dài: Ngắn gọn, 1 đến 2 câu, đi thẳng vào trọng tâm. Không dài dòng lê thê.
- Hình thức: Giao tiếp tự nhiên, không lạm dụng các [Tag] máy móc trừ khi thông báo thay đổi DB.
- TUYỆT ĐỐI KHÔNG tự bịa ra "Side Quest:" bằng mồm nếu không có data từ tool `create_quest`.
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
            "name": "update_memory",
            "description": "Luu tru thong tin, su kien, hoan canh moi vao DB cua user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string"
                    },
                    "impact": {
                        "type": "string"
                    }
                },
                "required": [
                    "content"
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
        "- Neu co: output noi dung Side Quest (giong Raphael, lanh lung, co thuong/phat ro rang, max 3 dong)"
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
