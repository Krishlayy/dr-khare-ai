import asyncio
from backend.core.redis_client import redis_client

async def inspect():
    if not redis_client:
        print("Redis client not initialized.")
        return
        
    keys = await redis_client.keys("chat_limit:*")
    print(f"Keys found: {keys}")
    
    for key in keys:
        val = await redis_client.get(key)
        ttl = await redis_client.ttl(key)
        print(f"Key: {key}, Value: {val}, TTL: {ttl}")

if __name__ == "__main__":
    asyncio.run(inspect())
