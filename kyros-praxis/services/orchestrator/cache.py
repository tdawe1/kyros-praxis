"""
Redis Cache Manager for Kyros Orchestrator

This module provides Redis-based caching for frequently accessed data to improve
database performance. It implements caching for:
- Job status counts
- User authentication data
- Recent events
- Job lists by status

The cache uses configurable TTL values and implements cache invalidation strategies
to ensure data consistency.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import redis
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from .models import Job, Event, User
except ImportError:
    from models import Job, Event, User


class CacheManager:
    """
    Redis cache manager for database query optimization.
    
    Provides caching for frequently accessed database queries with configurable
    TTL values and cache invalidation strategies.
    """
    
    def __init__(self):
        """Initialize Redis connection with environment configuration."""
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.redis_db = int(os.getenv('REDIS_DB', 0))
        self.redis_password = os.getenv('REDIS_PASSWORD', None)
        
        # Cache TTL values (in seconds)
        self.ttl_job_counts = int(os.getenv('CACHE_TTL_JOB_COUNTS', 300))  # 5 minutes
        self.ttl_job_list = int(os.getenv('CACHE_TTL_JOB_LIST', 60))      # 1 minute
        self.ttl_user_auth = int(os.getenv('CACHE_TTL_USER_AUTH', 900))   # 15 minutes
        self.ttl_events = int(os.getenv('CACHE_TTL_EVENTS', 30))          # 30 seconds
        
        # Initialize Redis connection
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            self.enabled = True
        except (redis.ConnectionError, redis.TimeoutError):
            # Fallback to no caching if Redis is not available
            self.redis_client = None
            self.enabled = False
    
    def _make_key(self, prefix: str, *args) -> str:
        """Create a cache key with consistent naming convention."""
        key_parts = [prefix] + [str(arg) for arg in args]
        return ':'.join(key_parts)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with JSON deserialization."""
        if not self.enabled:
            return None
            
        try:
            value = self.redis_client.get(key)
            if value is not None:
                return json.loads(value)
        except (redis.RedisError, json.JSONDecodeError):
            pass
        return None
    
    def set(self, key: str, value: Any, ttl: int) -> bool:
        """Set value in cache with JSON serialization and TTL."""
        if not self.enabled:
            return False
            
        try:
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(key, ttl, serialized_value)
        except (redis.RedisError, json.JSONEncodeError):
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.enabled:
            return False
            
        try:
            return bool(self.redis_client.delete(key))
        except redis.RedisError:
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        if not self.enabled:
            return 0
            
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
        except redis.RedisError:
            pass
        return 0
    
    # Job-related caching methods
    async def get_job_counts_by_status(self, db: AsyncSession) -> Dict[str, int]:
        """Get job counts by status with caching."""
        cache_key = self._make_key('job_counts')
        
        # Try cache first
        cached_counts = self.get(cache_key)
        if cached_counts is not None:
            return cached_counts
        
        # Query database
        result = await db.execute(
            select(Job.status, func.count(Job.id)).group_by(Job.status)
        )
        counts = dict(result.fetchall())
        
        # Cache the result
        self.set(cache_key, counts, self.ttl_job_counts)
        return counts
    
    async def get_jobs_by_status(self, db: AsyncSession, status: str, limit: int = 100) -> List[Dict]:
        """Get jobs by status with caching."""
        cache_key = self._make_key('jobs_by_status', status, limit)
        
        # Try cache first
        cached_jobs = self.get(cache_key)
        if cached_jobs is not None:
            return cached_jobs
        
        # Query database
        result = await db.execute(
            select(Job).where(Job.status == status)
            .order_by(Job.created_at.desc())
            .limit(limit)
        )
        jobs = result.scalars().all()
        
        # Serialize job data
        job_data = [
            {
                'id': job.id,
                'name': job.name,
                'status': job.status,
                'priority': job.priority,
                'created_at': job.created_at.isoformat() if job.created_at else None,
                'updated_at': job.updated_at.isoformat() if job.updated_at else None,
            }
            for job in jobs
        ]
        
        # Cache the result
        self.set(cache_key, job_data, self.ttl_job_list)
        return job_data
    
    async def get_recent_events(self, db: AsyncSession, limit: int = 100) -> List[Dict]:
        """Get recent events with caching."""
        cache_key = self._make_key('recent_events', limit)
        
        # Try cache first
        cached_events = self.get(cache_key)
        if cached_events is not None:
            return cached_events
        
        # Query database for recent events (last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        result = await db.execute(
            select(Event).where(Event.created_at > one_hour_ago)
            .order_by(Event.created_at.desc())
            .limit(limit)
        )
        events = result.scalars().all()
        
        # Serialize event data
        event_data = [
            {
                'id': event.id,
                'type': event.type,
                'payload': event.payload,
                'created_at': event.created_at.isoformat() if event.created_at else None,
            }
            for event in events
        ]
        
        # Cache the result with shorter TTL for events
        self.set(cache_key, event_data, self.ttl_events)
        return event_data
    
    async def get_user_by_username(self, db: AsyncSession, username: str) -> Optional[Dict]:
        """Get user by username with caching (for authentication)."""
        cache_key = self._make_key('user_auth', username)
        
        # Try cache first
        cached_user = self.get(cache_key)
        if cached_user is not None:
            return cached_user
        
        # Query database
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if user:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'password_hash': user.password_hash,
                'role': user.role,
                'active': user.active,
                'created_at': user.created_at.isoformat() if user.created_at else None,
            }
            # Cache user data with longer TTL
            self.set(cache_key, user_data, self.ttl_user_auth)
            return user_data
        
        return None
    
    # Cache invalidation methods
    def invalidate_job_cache(self, job_id: Optional[str] = None, status: Optional[str] = None):
        """Invalidate job-related cache entries."""
        # Always invalidate job counts
        self.delete(self._make_key('job_counts'))
        
        # Invalidate specific status cache if provided
        if status:
            self.delete_pattern(self._make_key('jobs_by_status', status, '*'))
        else:
            # Invalidate all job status caches
            self.delete_pattern(self._make_key('jobs_by_status', '*'))
    
    def invalidate_event_cache(self):
        """Invalidate event-related cache entries."""
        self.delete_pattern(self._make_key('recent_events', '*'))
    
    def invalidate_user_cache(self, username: Optional[str] = None):
        """Invalidate user-related cache entries."""
        if username:
            self.delete(self._make_key('user_auth', username))
        else:
            self.delete_pattern(self._make_key('user_auth', '*'))
    
    def health_check(self) -> Dict[str, Any]:
        """Check Redis connection health."""
        if not self.enabled:
            return {
                'status': 'disabled',
                'message': 'Redis caching is disabled',
                'connection': False
            }
        
        try:
            ping_result = self.redis_client.ping()
            info = self.redis_client.info()
            
            return {
                'status': 'healthy',
                'connection': ping_result,
                'memory_usage': info.get('used_memory_human', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'uptime_seconds': info.get('uptime_in_seconds', 0)
            }
        except redis.RedisError as e:
            return {
                'status': 'unhealthy',
                'connection': False,
                'error': str(e)
            }


# Global cache manager instance
cache_manager = CacheManager()