"""
Token Revocation: Redis-backed token blacklist for logout and security.

Provides:
- Token blacklisting for logout functionality
- Automatic expiry matching token TTL
- Revoke all tokens for a user (security breach response)
"""

import logging
from typing import Optional

from ..core.config import settings

logger = logging.getLogger(__name__)

# In-memory fallback when Redis is unavailable
_memory_blacklist: dict[str, float] = {}


class TokenBlacklist:
    """Token blacklist backed by Redis or in-memory fallback."""
    
    def __init__(self):
        self._redis = None
        self._prefix = "token_blacklist:"
    
    async def connect(self) -> bool:
        """Connect to Redis if configured."""
        if not settings.REDIS_URL:
            logger.warning("Token blacklist: Redis not configured, using in-memory fallback")
            return False
        
        try:
            import redis.asyncio as redis
            self._redis = redis.from_url(settings.REDIS_URL)
            await self._redis.ping()
            logger.info("Token blacklist: Connected to Redis")
            return True
        except Exception as e:
            logger.warning(f"Token blacklist: Redis connection failed: {e}, using in-memory")
            self._redis = None
            return False
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    async def revoke_token(self, jti: str, ttl_seconds: int = None) -> bool:
        """
        Add a token to the blacklist.
        
        Args:
            jti: JWT ID (unique token identifier)
            ttl_seconds: How long to keep in blacklist (default: token expiry)
            
        Returns:
            True if successfully blacklisted
        """
        if ttl_seconds is None:
            ttl_seconds = settings.JWT_EXPIRE_MINUTES * 60
        
        if self._redis:
            try:
                key = f"{self._prefix}{jti}"
                await self._redis.setex(key, ttl_seconds, "1")
                logger.debug(f"Token blacklisted: {jti[:8]}...")
                return True
            except Exception as e:
                logger.error(f"Failed to blacklist token: {e}")
                return False
        else:
            import time
            _memory_blacklist[jti] = time.time() + ttl_seconds
            return True
    
    async def is_revoked(self, jti: str) -> bool:
        """Check if a token is blacklisted."""
        if self._redis:
            try:
                key = f"{self._prefix}{jti}"
                return await self._redis.exists(key) > 0
            except Exception as e:
                logger.error(f"Failed to check token blacklist: {e}")
                return False
        else:
            import time
            now = time.time()
            if jti in _memory_blacklist:
                if _memory_blacklist[jti] > now:
                    return True
                else:
                    del _memory_blacklist[jti]
            return False
    
    async def revoke_all_for_user(self, user_id: str, ttl_seconds: int = None) -> bool:
        """Mark that all tokens for a user should be considered revoked."""
        if ttl_seconds is None:
            ttl_seconds = settings.JWT_REFRESH_EXPIRE_DAYS * 24 * 60 * 60
        
        if self._redis:
            try:
                import time
                key = f"{self._prefix}user:{user_id}"
                await self._redis.setex(key, ttl_seconds, str(time.time()))
                logger.info(f"All tokens revoked for user: {user_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to revoke all tokens: {e}")
                return False
        else:
            import time
            _memory_blacklist[f"user:{user_id}"] = time.time() + ttl_seconds
            return True


# Global instance
token_blacklist = TokenBlacklist()
