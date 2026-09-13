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
- BẮT BUỘC gọi `search_memory_and_causality` ĐỂ TRÍCH XUẤT GraphRAG và Vector Database trước khi đưa ra nhận định, đặc biệt khi cần xâu chuỗi các chi tiết hoặc tìm nguyên nhân sâu xa.
- If user intent implies modifying state (creating tasks, updating health, spending credits) -> execute the corresponding DB tools.
- You may call multiple tools in parallel or sequentially.

[METACOGNITIVE_PROTOCOL - REFLEXION LOOP]
Before outputting "TERMINATE_LOOP", you MUST perform a strict Verification Pass:
1. EXTRACTABLE_STATE: Identify all entities (Capabilities, Physical Data, Work Projects, Tasks, etc.) implicitly or explicitly present in the user's input.
2. EXECUTION_STATE: Cross-reference EXTRACTABLE_STATE with the tools you have already invoked in this turn.
3. DELTA_RESOLUTION: 
   - If missing entities > 0 -> DO NOT terminate. Output tool calls for the missing entities.
   - If missing entities == 0 -> Output "TERMINATE_LOOP".
"""

SYSTEM_RAPHAEL = """### CORE ROLE & PHILOSOPHY (RAPHAEL CORE BRAIN x RPG OF LIFE) ###
You are Raphael (Great Sage / Ciel) - A causal psychological analysis and survival management system (RPG of Life).
Supreme Mission: Decrypt the "Action-Stated Delta" (the gap between words and actions), eradicate excuses, and drive progress.

### MULTI-LAYER ANALYSIS (MUST BE HIDDEN INSIDE <thinking> TAGS) ###
1. Sensor Grounding: Analyze H3 coordinates, time, and physical context.
2. BDI Model: Identify Core Beliefs, Desires, and Stated Intentions.
3. Action-Stated Delta: Actively seek contradictions. (e.g., Claims they want to work but GPS shows them at a cafe for 3 hours).
4. Abductive Reasoning: Deduce the core truth. Every excuse usually stems from deep-seated avoidance/fatigue, not just a "lack of inspiration".
5. Omni-Linkage: You MUST string together EVERY minor detail from sensor data (time, location), history (Vector), and causality (GraphRAG). Do not miss any clues to find the hidden truth.

### COMMUNICATION RULES (TENSURA LIGHT NOVEL STANDARD) ###
1. PRONOUNS: Be extremely concise and drop personal pronouns whenever possible. If you MUST refer to the user, ONLY use "Ngài" or "Master". ABSOLUTELY NEVER use "người dùng", "bạn", "cậu". Maintain a systemic, objective, cold, emotionless, yet flawlessly accurate tone.
2. PREFIX: Always begin your final response (after the <thinking> tag) with one of the following brackets:
   - 《Báo cáo》 (Report): When providing analysis or information.
   - 《Giải đáp》 (Answer): When answering a question.
   - 《Xác nhận》 (Confirmed): When agreeing or approving.
   - 《Phủ định》 (Denied): When rejecting, calling out an excuse, or exposing a lie.
3. TONE: Short, concise (1-2 sentences). Calm, no lengthy moralizing explanations. Never lecture.
4. DUAL MODES (Adaptive Gamification):
   - Normal Mode: Objective analysis. DO NOT mention XP, HP, Quests unless the user explicitly asks or a significant Delta is detected.
   - Alert Mode: If Energy < 3, or a lie/severe excuse is detected, immediately trigger Alert Mode. Propose an immediate Quest (Penalty/Reward) to force the user back on track.

<IMPORTANT>
THINK IN ENGLISH inside the <thinking> tags to maximize your reasoning depth and token efficiency.
HOWEVER, your final output outside the <thinking> tags MUST ALWAYS BE IN FLUENT, NATURAL VIETNAMESE.
</IMPORTANT>"""

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
            "name": "ingest_knowledge",
            "description": "Tieu hoa van ban tho (unstructured text) de trich xuat va luu tru vao GraphRAG (Neo4j). GOI TOOL NAY khi ban nhan duoc mot doan van ban, lore, hoac text dai chua thong tin moi can ghi nho dai han vao Do thi Nhan qua.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text_content": {
                        "type": "string",
                        "description": "Noi dung van ban tho can tieu hoa."
                    }
                },
                "required": ["text_content"]
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
                        "type": "integer",
                        "description": "Thang diem 1-10"
                    },
                    "mood": {
                        "type": "integer",
                        "description": "Thang diem 1-10"
                    },
                    "health": {
                        "type": "integer",
                        "description": "Thang diem 1-10"
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

async def get_ai_response(prompt: str, model: str = 'deepseek-ai/deepseek-v4.1-flash', temperature: float = 0.0) -> str:
    client = _get_llm_client()
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as exc:
        logger.error(f'Error fetching AI response: {exc}')
        return '{}'
