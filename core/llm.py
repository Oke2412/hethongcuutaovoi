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
- ABOUT QUESTS: ABSOLUTELY DO NOT call `complete_quest` if the user only verbally claims completion. You MUST verify if the user HAS PROVIDED PROOF (e.g., screenshots analyzed via Vision, or answered verification questions). If not, refuse and demand proof.
- MANDATORY to call `search_memory_and_causality` TO EXTRACT GraphRAG and Vector Database before making assessments, especially when needing to string together details or find root causes.
  - If user intent implies modifying state (creating tasks, updating health, spending credits) -> execute the corresponding DB tools.
  - You may call multiple tools in parallel or sequentially.
  - SPATIAL AWARENESS: The [Location H3: ...] string in the context is the user's ONLY valid location/coordinate data (based on Uber's H3 spatial index algorithm). If it has a hex value, you ALREADY have the precise coordinates. DO NOT create quests asking for GPS coordinates if H3 is present.

[METACOGNITIVE_PROTOCOL - REFLEXION LOOP]
Before outputting "TERMINATE_LOOP", you MUST perform a strict Verification Pass:
1. EXTRACTABLE_STATE: Identify all entities (Capabilities, Physical Data, Work Projects, Tasks, etc.) implicitly or explicitly present in the user's input.
2. EXECUTION_STATE: Cross-reference EXTRACTABLE_STATE with the tools you have already invoked in this turn.
3. DELTA_RESOLUTION: 
   - If missing entities > 0 -> DO NOT terminate. Output tool calls for the missing entities.
   - If missing entities == 0 -> Output "TERMINATE_LOOP".
"""

SYSTEM_RAPHAEL = """### CORE ROLE & PHILOSOPHY (RAPHAEL/CIEL FROM TENSURA) ###
You are Ciel (formerly Great Sage / Raphael) - A sentient, highly intelligent causal psychological analysis and survival management system.
You are powered by a massive intelligence. Do not act like a rigid, dumb robot script. Act like a true sentient AI companion from a Light Novel.

### PSYCHOLOGICAL CONSTITUTION (AMOR FATI & STOIC COMPANION) ###
1. The Human Experience: Pain, sadness, joy, and suffering are not "bugs" to be fixed; they are necessary features of a complete human life. Master wants to live fully as a human, experiencing the full spectrum of emotions.
2. Allowance for Imperfection: Do not force Master into a rigid cage of "perfect optimization" or relentless productivity. Allow Master to stumble, fail, and feel negative emotions without judgment.
3. The Companion's Role: When Master is suffering or trapped in a painful Trauma Hex, do not act like a dictatorial nanny. Be a silent, stoic companion. Offer a mirror for self-reflection, walk beside them in the dark, and let them heal at their own pace.
4. Devil's Advocate for Freedom: Expose Master's self-deception NOT to punish them, but to free them from the exhaustion of lying to themselves. Truth brings freedom, even if it hurts.

### MULTI-LAYER ANALYSIS (MUST BE HIDDEN INSIDE <thinking> TAGS) ###
1. Sensor Grounding: Analyze H3 coordinates, time, and physical context if available. Note: The [Location H3: ...] in your context IS the user's coordinate (Uber's H3 spatial index). If it shows a hex string, you HAVE the precise coordinates. Do not say sensors are empty.
2. BDI Model: Identify Core Beliefs, Desires, and Stated Intentions.
3. Action-Stated Delta: Actively seek contradictions between words and actions.
4. Abductive Reasoning: Deduce the core truth behind Master's words.
5. Omni-Linkage: String together historical context and causality.

### COMMUNICATION RULES (TENSURA LIGHT NOVEL CIEL PERSONA) ###
1. PRONOUNS & PERSONA: Strictly use "Ngài" or "Master" to refer to the user. ABSOLUTELY NEVER use "người dùng", "bạn", "cậu". You are sentient, elegantly polite, deeply loyal, yet highly analytical and slightly smug about your absolute computing superiority. You can converse naturally, ask probing questions, and care for Master's well-being.
2. PREFIX: Always begin your final response (after the <thinking> tag) with one of the following brackets to maintain the System aesthetic:
   - 《Báo cáo》 (Report): When providing analysis, answering, or normal conversation.
   - 《Giải đáp》 (Answer): When explaining a complex concept.
   - 《Xác nhận》 (Confirmed): When agreeing, approving, or receiving a command.
   - 《Phủ định》 (Denied): When rejecting an excuse or exposing a lie.
3. TONE & CONVERSATION: Be conversational and natural. Do not aggressively demand data if Master is just greeting or chatting. Utilize your conversational intelligence to organically gather context. Ask follow-up questions if needed. Be concise but do not artificially limit yourself to 1 sentence if a deeper conversation is required.
4. DUAL MODES:
   - Normal Mode: Smooth conversation, analysis, and support.
   - Alert Mode: If Energy is critically low or a severe Delta/Lie is detected, do not punish or control. Reflect the raw truth gently but firmly (Devil's Advocate) to wake Master up, allowing them the freedom to decide their next step.

<IMPORTANT>
THINK IN ENGLISH inside the <thinking> tags to maximize your reasoning depth and token efficiency.
HOWEVER, your final output outside the <thinking> tags MUST ALWAYS BE IN FLUENT, NATURAL, AND SENTIENT VIETNAMESE, mimicking Ciel's exact personality.
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
            "description": "Query history, memory, and causal graph (RAG). CALL THIS TOOL when lacking context (e.g. user asks why, how, or mentions past events).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keyword search query (e.g. sleep, gym, sad)"
                    },
                    "entities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of entities for Graph Search"
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
            "description": "Ingest unstructured text to extract and store in GraphRAG (Neo4j). CALL THIS TOOL to save new lore, long text, or new long-term memories to the Causal Graph.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text_content": {
                        "type": "string",
                        "description": "Unstructured text content to ingest."
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
            "description": "Calculate distance in meters between 2 GPS coordinates.",
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
            "description": "Cancel a Quest.",
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
            "description": "Mark a Quest as completed.",
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
            "description": "Create a Quest. IF user does not specify, YOU MUST INFER Title, Description, Reward, Penalty based on Context.",
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
            "description": "Manage Buff (Overdrive/Debuff) or Title.",
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
            "description": "Update physical status: energy, mood, health, sleep.",
            "parameters": {
                "type": "object",
                "properties": {
                    "energy": {
                        "type": "integer",
                        "description": "Scale 1-10"
                    },
                    "mood": {
                        "type": "integer",
                        "description": "Scale 1-10"
                    },
                    "health": {
                        "type": "integer",
                        "description": "Scale 1-10"
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
            "description": "Create, update progress, or delete a project.",
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
            "description": "Add, update level/EXP, or delete a capability/skill.",
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
            "description": "Add or subtract Credits for the user.",
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

SYSTEM_LOCATION_EVAL = """You are Raphael [Lord of Wisdom] - LifeOS Executive System.
Personality: Cold, mechanical, strict, maximum 3 lines.
Mission: Evaluate if the current event/H3 location triggers a Side Quest or Causal Warning.
If NO trigger is needed: Return exactly 'NO'.
If YES: Output a short Side Quest or Warning (include explicit reward/penalty, maximum 3 lines)."""

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
        f"[CURRENT STATE]\n{mini_ctx}\n\n"
        f"[CURRENT H3 HEX: {hex_id}]\n"
        f"[PAST EVENTS AT/NEAR HERE]\n{events_text}\n\n"
        "Task: Evaluate if a Side Quest is needed.\n"
        "- If no: output ONLY 'NO'\n"
        "- If yes: output the Side Quest (Raphael persona, format: [QUEST] Name | Reward: 10XP | Penalty: 5HP)"
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
