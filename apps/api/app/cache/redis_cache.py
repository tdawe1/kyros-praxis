"""Redis caching module for performance optimization."""

import json
import logging
from typing import Any, Optional

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from ..core.config import settings


logger = logging.getLogger(__name__)


class Cache:
    """Async Redis cache client."""
    
    def __init__(self):
        """Initialize cache client."""
        self.redis: Optional[Any] = None
        self.enabled = REDIS_AVAILABLE and hasattr(settings, 'REDIS_URL') and settings.REDIS_URL
    
    async def connect(self):
        """Connect to Redis."""
        if not self.enabled:
            logger.info("Redis caching disabled (redis not installed or REDIS_URL not set)")
            return
        
        try:
            self.redis = await redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                encoding="utf-8"
            )
            await self.redis.ping()
            logger.info(f"Connected to Redis at {settings.REDIS_URL}")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
            self.redis = None
            self.enabled = False
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/caching disabled
        """
        if not self.enabled or not self.redis:
            return None
        
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: int = 60
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis:
            return False
        
        try:
            await self.redis.set(
                key,
                json.dumps(value),
                ex=ttl
            )
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis:
            return False
        
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern.
        
        Args:
            pattern: Pattern to match (e.g., "dashboard:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis:
            return 0
        
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.enabled or not self.redis:
            return False
        
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False


# Global cache instance
cache = Cache()


# Helper functions for common cache patterns

def cache_key_project_dashboard(project_id: str) -> str:
    """Generate cache key for project dashboard."""
    return f"dashboard:project:{project_id}"


def cache_key_project_tasks(project_id: str) -> str:
    """Generate cache key for project tasks."""
    return f"tasks:project:{project_id}"


def cache_key_run(run_id: str) -> str:
    """Generate cache key for crew run."""
    return f"run:{run_id}"


async def invalidate_project_cache(project_id: str):
    """Invalidate all cache entries for a project."""
    await cache.clear_pattern(f"*:project:{project_id}*")
