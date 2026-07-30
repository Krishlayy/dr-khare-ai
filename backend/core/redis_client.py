from redis import asyncio as aioredis
from backend.core.config import settings

redis_client = None

if settings.REDIS_URL:
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
