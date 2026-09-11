import json
import httpx
import logging
from typing import List, Dict, Any
from config import settings
from db.database import AsyncSessionLocal
from sqlalchemy import text

logger = logging.getLogger(__name__)

async def sparse_search(keywords: List[str], limit: int = 5) -> List[str]:
    """Khâu 2: Sparse Search (BM25) via SQLite FTS5."""
    query_str = " OR ".join([f'"{k}"' for k in keywords]) # Simple OR matching
    
    try:
        async with AsyncSessionLocal() as session:
            stmt = text("""
                SELECT content 
                FROM messagelog_fts 
                WHERE messagelog_fts MATCH :query 
                ORDER BY rank 
                LIMIT :limit
            """)
            result = await session.execute(stmt, {"query": query_str, "limit": limit})
            rows = result.fetchall()
            return [row[0] for row in rows]
    except Exception as e:
        logger.warning(f"Sparse search failed: {e}")
        return []


async def rerank_chunks(query: str, chunks: List[str], top_k: int = 3) -> List[str]:
    """Khâu 3: Reranking Vòng 2 via OpenRouter API."""
    if not chunks:
        return []
    if len(chunks) <= top_k:
        return chunks
        
    api_key = settings.siliconflow_api_key
    url = settings.reranker_api_url
    
    if not api_key:
        logger.warning("No SILICONFLOW_API_KEY provided, skipping reranking.")
        return chunks[:top_k]
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "Qwen/Qwen3-Reranker-8B",
        "query": query,
        "documents": chunks,
        "top_n": top_k
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # OpenRouter typically returns {"results": [{"index": 0, "relevance_score": 0.9}, ...]}
            results = data.get("results", [])
            results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            reranked_chunks = [chunks[r["index"]] for r in results[:top_k]]
            return reranked_chunks
    except Exception as e:
        logger.warning(f"Reranking API failed: {e}")
        return chunks[:top_k]
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "BAAI/bge-reranker-v2-m3", # Standard fallback reranker on SiliconFlow. Adjust to Qwen if SiliconFlow changes endpoint names.
        "query": query,
        "texts": chunks,
        "top_n": top_k
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # SiliconFlow/DashScope typically returns {"results": [{"index": 0, "relevance_score": 0.9}, ...]}
            results = data.get("results", [])
            # Sort just in case, though API usually sorts it
            results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            reranked_chunks = [chunks[r["index"]] for r in results[:top_k]]
            return reranked_chunks
    except Exception as e:
        logger.warning(f"Reranking API failed: {e}")
        return chunks[:top_k]
