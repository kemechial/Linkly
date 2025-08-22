from typing import Optional, Dict
import json
from app.redis_config import get_sync_redis_client
from app.logging_config import get_logger

logger = get_logger("redis_cache")

class LinkCache:
    def __init__(self):
        self.redis = get_sync_redis_client()
        self.cache_prefix = "link:"
        self.clicks_prefix = "clicks:"
        self.cache_ttl = 3600  # 1 hour
        logger.info("Redis LinkCache initialized")
        
    def get_link(self, short_key: str) -> Optional[Dict[str, any]]:
        """Get link data from Redis cache"""
        try:
            data = self.redis.get(f"{self.cache_prefix}{short_key}")
            if data:
                logger.info(f"✅ CACHE HIT: {short_key} -> Retrieved from Redis")
                return json.loads(data)
            else:
                logger.info(f"❌ CACHE MISS: {short_key} -> Not found in Redis")
        except Exception as e:
            logger.error(f"🔥 Redis ERROR for {short_key}: {e}")
        return None
    
    def set_link(self, short_key: str, target_url: str) -> None:
        """Cache link target URL in Redis"""
        try:
            cache_data = {"target_url": target_url}
            self.redis.setex(
                f"{self.cache_prefix}{short_key}",
                self.cache_ttl,
                json.dumps(cache_data)
            )
            logger.info(f"💾 CACHED: {short_key} -> {target_url} (TTL: {self.cache_ttl}s)")
        except Exception as e:
            logger.error(f"🔥 Redis SET failed for {short_key}: {e}")
    
    def delete_link(self, short_key: str) -> None:
        """Remove link from cache"""
        try:
            self.redis.delete(f"{self.cache_prefix}{short_key}")
            self.redis.delete(f"{self.clicks_prefix}{short_key}")
            logger.info(f"🗑️  DELETED: {short_key} removed from cache")
        except Exception as e:
            logger.error(f"🔥 Redis DELETE failed for {short_key}: {e}")
    
    def increment_clicks(self, short_key: str) -> int:
        """Increment and get click count in Redis"""
        try:
            # Increment click counter
            new_count = self.redis.incr(f"{self.clicks_prefix}{short_key}")
            # Set expiration to match cache TTL
            self.redis.expire(f"{self.clicks_prefix}{short_key}", self.cache_ttl)
            logger.info(f"📈 CLICK: {short_key} -> Click #{new_count}")
            return new_count
        except Exception as e:
            logger.error(f"🔥 Redis INCREMENT failed for {short_key}: {e}")
            return 0
    
    def get_clicks(self, short_key: str) -> int:
        """Get current click count from Redis"""
        try:
            clicks = self.redis.get(f"{self.clicks_prefix}{short_key}")
            count = int(clicks) if clicks else 0
            logger.debug(f"📊 CLICKS: {short_key} has {count} clicks in Redis")
            return count
        except Exception as e:
            logger.error(f"🔥 Redis GET CLICKS failed for {short_key}: {e}")
            return 0

# Create singleton instance
link_cache = LinkCache()