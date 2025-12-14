"""Request correlation ID middleware for distributed tracing."""

import logging
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger(__name__)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation IDs to requests.
    
    Correlation IDs help track requests across multiple services and logs.
    If a correlation ID is provided in the X-Correlation-ID header, it will be used.
    Otherwise, a new UUID will be generated.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and add correlation ID.
        
        Args:
            request: Incoming request
            call_next: Next middleware in chain
            
        Returns:
            Response with correlation ID header
        """
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        
        # Store in request state for access in route handlers
        request.state.correlation_id = correlation_id
        
        # Add to logger context (if using structured logging)
        # This would require a custom logging filter
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response


def get_correlation_id(request: Request) -> str:
    """
    Get correlation ID from request state.
    
    Usage in route handlers:
        correlation_id = get_correlation_id(request)
        logger.info(f"Processing request {correlation_id}")
    
    Args:
        request: FastAPI request object
        
    Returns:
        Correlation ID string
    """
    return getattr(request.state, "correlation_id", "unknown")
