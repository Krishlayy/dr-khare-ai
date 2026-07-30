import json
import logging
from backend.core.redis_client import redis_client

logger = logging.getLogger(__name__)

CACHE_TTL = 3600 * 24 * 7  # 7 days

def _normalize_question(question: str) -> str:
    # Basic normalization: lower case, strip whitespace, remove basic punctuation at the end
    q = question.strip().lower()
    if q.endswith('?') or q.endswith('.'):
        q = q[:-1]
    return q.strip()

async def get_cached_answer(question: str) -> dict | None:
    if not redis_client:
        return None
        
    try:
        normalized = _normalize_question(question)
        key = f"chat_cache:{normalized}"
        
        cached_data = await redis_client.get(key)
        if cached_data:
            logger.info(f"Cache hit for normalized question: '{normalized}'")
            return json.loads(cached_data)
        return None
    except Exception as e:
        logger.error(f"Redis cache read error: {e}")
        return None

async def set_cached_answer(question: str, result: dict) -> None:
    if not redis_client:
        return
        
    try:
        # Don't cache hard grounding responses or off-topic refusals (only cache high confidence LLM responses)
        # Actually, caching refusals might save LLM cost too, but let's cache everything that is a final dict.
        # But wait, we only want to cache the "response", "sources", "confidence", "answer_source".
        normalized = _normalize_question(question)
        key = f"chat_cache:{normalized}"
        
        cache_payload = {
            "response": result["response"],
            "sources": result["sources"],
            "confidence": result["confidence"],
            "answer_source": result["answer_source"],
            "model": "cache",
            "bypassed_llm": True
        }
        
        await redis_client.setex(key, CACHE_TTL, json.dumps(cache_payload))
    except Exception as e:
        logger.error(f"Redis cache write error: {e}")
