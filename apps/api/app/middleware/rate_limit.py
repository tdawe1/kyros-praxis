"""Rate limiting middleware to prevent abuse."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import Request, HTTPException, status


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, requests_per_minute: int = None):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute per IP (defaults to config)
        """
        from ..core.config import settings
        self.requests_per_minute = requests_per_minute or settings.RATE_LIMIT_RPM
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
    
    async def check(self, request: Request) -> None:
        """
        Check if request should be rate limited.
        
        Args:
            request: FastAPI request object
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        # Skip rate limiting for health check
        if request.url.path == "/health":
            return
        
        client_ip = request.client.host if request.client else "unknown"
        now = datetime.now()
        
        # Clean old requests (older than 1 minute)
        cutoff = now - timedelta(minutes=1)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > cutoff
        ]
        
        # Check limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.requests_per_minute} requests per minute allowed",
                    "retry_after": 60  # seconds
                }
            )
        
        # Add current request
        self.requests[client_ip].append(now)
    
    def get_stats(self, client_ip: str) -> Dict:
        """Get rate limit stats for a client."""
        cutoff = datetime.now() - timedelta(minutes=1)
        recent = [r for r in self.requests.get(client_ip, []) if r > cutoff]
        
        return {
            "requests_in_last_minute": len(recent),
            "limit": self.requests_per_minute,
            "remaining": max(0, self.requests_per_minute - len(recent))
        }


# Global rate limiter instance (uses config value)
rate_limiter = RateLimiter()
