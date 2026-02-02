import json
import redis.asyncio as redis
from typing import Optional, Any
from src.config import settings
from functools import wraps
from datetime import datetime


class CacheService:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            await self.connect()
        
        value = await self.redis_client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL (seconds)"""
        if not self.redis_client:
            await self.connect()
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        await self.redis_client.setex(key, ttl, value)

    async def delete(self, key: str):
        """Delete key from cache"""
        if not self.redis_client:
            await self.connect()
        
        await self.redis_client.delete(key)

    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        if not self.redis_client:
            await self.connect()
        
        keys = []
        async for key in self.redis_client.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            await self.redis_client.delete(*keys)

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.redis_client:
            await self.connect()
        
        return await self.redis_client.exists(key) > 0


# Singleton instance
cache_service = CacheService()


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching function results.
    
    Usage:
        @cached(ttl=300, key_prefix="dashboard_stats")
        async def get_dashboard_stats():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}"
            if args:
                cache_key += f":{':'.join(str(arg) for arg in args)}"
            if kwargs:
                cache_key += f":{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
            
            # Try to get from cache
            cached_value = await cache_service.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache_service.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator
