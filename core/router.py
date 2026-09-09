import re, unicodedata
from google import genai
import asyncio

def _normalize(text: str) -> str:
    """Strip diacritics for Vietnamese matching."""
    return unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode()

# Data patterns (cả có dấu lẫn không dấu)
DATA_KEYWORDS = [
    r"\b(can|kg|kilo|chieu cao|cm|bmi|ngu|giac ngu|nang luong|energy|suc khoe|dau|om|tam trang|mood|gay|thuong|benh|huyet ap|nhip tim|met|yeu|soc|chan|tay|dau|lung)\b",
    r"\b(hoc|tap|luyen|code|viet|doc|skill|level|exp|du an|project|tien do|xong|done|hoàn thành|hoàn tất)\b",
    r"\b(quest|nhiem vu|task|huy|cancel|reward|credits|tin chi)\b",
    r"\b\d+\s*(kg|cm|h|gio|phut|%|diem|exp)\b",
]

DEEP_KEYWORDS = [
    r"\b(phan tich|phan tích|ke hoach|kế hoạch|lich|lịch|tuần|thang|tháng|muc tieu|mục tiêu|vì sao|tai sao|tại sao)\b",
]

def classify_message(text: str) -> str:
    """Returns: 'chat' | 'data' | 'deep'"""
    norm = _normalize(text.lower())
    if any(re.search(p, norm) for p in DEEP_KEYWORDS):
        return "deep"
    if any(re.search(p, norm) for p in DATA_KEYWORDS):
        return "data"
    return "chat"

ROUTER_ANCHORS = {
    "data": "can nang hoc tap ngu du an tien do ky nang exp level",
    "chat": "met moi buon vui cam xuc than van chia se cam giac",
    "deep": "phan tich ke hoach muc tieu tai sao ly do chien luoc",
}

import math

def _cosine_sim(v1: list[float], v2: list[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

async def semantic_classify(text: str, client: genai.Client) -> str:
    try:
        # Generate embeddings in one batch
        contents = [
            text,
            "cân nặng 70kg, ngủ 6 tiếng, học Python 2 giờ",
            "hôm nay mệt quá, không muốn làm gì",
            "phân tích tại sao tôi hay bị trễ deadline"
        ]
        
        response = await asyncio.to_thread(
            client.models.embed_content,
            model="gemini-embedding-2-preview",
            contents=contents,
        )
        
        embeddings = [emb.values for emb in response.embeddings]
        msg_emb = embeddings[0]
        anchors = {
            "data": embeddings[1],
            "chat": embeddings[2],
            "deep": embeddings[3]
        }
        
        best_match = "chat"
        best_score = -1.0
        for category, anchor_emb in anchors.items():
            score = _cosine_sim(msg_emb, anchor_emb)
            if score > best_score:
                best_score = score
                best_match = category
                
        return best_match
    except Exception as exc:
        return classify_message(text)
