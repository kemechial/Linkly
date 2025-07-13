import redis
from redis import asyncio as aioredis
from typing import Optional
import os
from functools import lru_cache

class RedisClient:
    def __init__(self):
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_url = f"redis://{host}:{port}/0"
        self.client: Optional[aioredis.Redis] = None
        
    async def get_client(self) -> aioredis.Redis:
        if not self.client:
            self.client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self.client
    
    async def close(self):
        if self.client:
            await self.client.close()

@lru_cache()
def get_redis_client() -> RedisClient:
    return RedisClient()

# Synchronous client for non-async operations
def get_sync_redis_client() -> redis.Redis:
    return redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        encoding="utf-8",
        decode_responses=True
    )