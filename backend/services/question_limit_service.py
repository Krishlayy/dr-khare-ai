import time
import logging
from backend.core.redis_client import redis_client

logger = logging.getLogger(__name__)

LIMIT = 5
WINDOW_SECONDS = 6 * 3600  # 6 hours

async def get_remaining_questions(user_identifier: str, is_admin: bool = False) -> dict:
    if is_admin:
        return {"remaining": "unlimited", "reset_in_seconds": 0}
        
    if not redis_client:
        return {"remaining": LIMIT, "reset_in_seconds": 0}
        
    key = f"chat_limit:{user_identifier}"
    
    try:
        count = await redis_client.get(key)
        if count is None:
            return {"remaining": LIMIT, "reset_in_seconds": 0}
            
        count = int(count)
        remaining = max(0, LIMIT - count)
        ttl = await redis_client.ttl(key)
        ttl = max(0, ttl)
        
        return {"remaining": remaining, "reset_in_seconds": ttl}
    except Exception as e:
        logger.error(f"Redis error getting remaining questions: {e}")
        return {"remaining": LIMIT, "reset_in_seconds": 0}

async def check_and_increment_limit(user_identifier: str, is_admin: bool = False) -> bool:
    if is_admin:
        return True
        
    if not redis_client:
        return True
        
    key = f"chat_limit:{user_identifier}"
    
    try:
        count = await redis_client.get(key)
        if count is not None and int(count) >= LIMIT:
            logger.info(f"Rate limit exceeded for user {user_identifier}")
            return False
            
        async with redis_client.pipeline() as pipe:
            pipe.incr(key)
            if count is None:
                pipe.expire(key, WINDOW_SECONDS)
            await pipe.execute()
        return True
    except Exception as e:
        logger.error(f"Redis error in check_and_increment_limit: {e}")
        return True
