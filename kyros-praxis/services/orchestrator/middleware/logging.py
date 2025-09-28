"""
Request Logging and Monitoring Middleware

This module provides comprehensive request logging and monitoring middleware
for the Kyros Orchestrator service. It tracks all incoming requests, records
timing information, extracts client details, and logs both successful responses
and errors for observability and debugging purposes.

The middleware also integrates with the orchestrator's event logging system
to provide a complete audit trail of all API interactions.
"""

import time
import logging
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from ..app.core.logging import get_request_logger, log_orchestrator_event
except ImportError:
    # Fallback implementations for environments where logging utilities are not available
    def get_request_logger(request_id=None, user_id=None, client_ip=None):
        """
        Fallback request logger implementation.
        
        Args:
            request_id: Unique identifier for the request
            user_id: Authenticated user identifier
            client_ip: Client IP address
            
        Returns:
            Logger: Request logger instance
        """
        logger = logging.getLogger('request')
        return logger
    
    def log_orchestrator_event(event, **kwargs):
        """
        Fallback orchestrator event logger.
        
        Args:
            event: Event type identifier
            **kwargs: Additional event data
        """
        pass


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request logging and monitoring.
    
    This middleware provides detailed logging of all HTTP requests and responses,
    including timing information, client details, and error tracking. It generates
    unique request IDs for tracing and integrates with the orchestrator's event
    logging system for comprehensive audit trails.
    
    Key features:
    - Request/response timing and performance monitoring
    - Client IP address extraction with proxy support
    - User identification from JWT tokens
    - Structured logging with rich metadata
    - Error tracking with full exception information
    - Request ID injection in response headers for client-side tracing
    - Integration with orchestrator event logging
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process incoming requests and log details.
        
        This method is called for each incoming HTTP request. It generates a
        unique request ID, extracts client information, logs the request start,
        processes the request through the application, and logs the response
        or any errors that occur.
        
        Args:
            request (Request): The incoming HTTP request
            call_next (Callable): Function to call the next middleware or route handler
            
        Returns:
            Response: The HTTP response from the application
            
        Raises:
            Exception: Any exception that occurs during request processing
        """
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())[:8]

        # Extract client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "unknown")

        # Extract user ID if available (from JWT token)
        user_id = self._extract_user_id(request)

        # Create request logger with context
        logger = get_request_logger(
            request_id=request_id,
            user_id=user_id,
            client_ip=client_ip
        )

        # Log request start
        start_time = time.time()
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.url.query),
                "user_agent": user_agent,
                "content_length": request.headers.get("content-length"),
            }
        )

        # Log orchestrator event for request start
        log_orchestrator_event(
            event="request_started",
            task_id=request_id,
            method=request.method,
            path=request.url.path,
            user_id=user_id,
            client_ip=client_ip
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate response time
            process_time = time.time() - start_time

            # Log successful response
            logger.info(
                f"Request completed: {response.status_code} in {process_time:.3f}s",
                extra={
                    "status_code": response.status_code,
                    "response_time": round(process_time * 1000, 2),  # ms
                    "response_length": response.headers.get("content-length"),
                }
            )

            # Log orchestrator event for successful response
            log_orchestrator_event(
                event="request_completed",
                task_id=request_id,
                status_code=response.status_code,
                response_time=round(process_time * 1000, 2),
                user_id=user_id
            )

            # Add request ID to response headers for client-side tracing
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate error response time
            process_time = time.time() - start_time

            # Log error
            logger.error(
                f"Request failed: {str(e)} in {process_time:.3f}s",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "response_time": round(process_time * 1000, 2),
                },
                exc_info=True
            )

            # Log orchestrator event for error response
            log_orchestrator_event(
                event="request_failed",
                task_id=request_id,
                error=str(e),
                error_type=type(e).__name__,
                response_time=round(process_time * 1000, 2),
                user_id=user_id
            )

            # Re-raise the exception
            raise

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request with proxy support.
        
        Attempts to extract the real client IP address, taking into account
        various proxy headers that may be present in load-balanced or
        reverse-proxy environments.
        
        Args:
            request (Request): The incoming HTTP request
            
        Returns:
            str: The client IP address or 'unknown' if it cannot be determined
        """
        # Check for forwarded headers (common with load balancers and reverse proxies)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Check for other proxy headers
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client
        if hasattr(request, 'client') and request.client:
            return request.client.host or "unknown"

        return "unknown"

    def _extract_user_id(self, request: Request) -> str:
        """
        Extract user ID from JWT token if present.
        
        Attempts to extract the user ID from the Authorization header if it
        contains a valid JWT token. This allows for user-specific logging
        and monitoring.
        
        Args:
            request (Request): The incoming HTTP request
            
        Returns:
            str: The user ID from the JWT token, or 'anonymous' if not available
        """
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # Basic JWT parsing to extract user ID
                # In production, you'd want more robust parsing
                import jwt
                try:
                    from ..app.core.config import settings
                    token = auth_header.split(" ")[1]
                    payload = jwt.decode(
                        token,
                        settings.SECRET_KEY,
                        algorithms=[settings.JWT_ALGORITHM],
                        options={"verify_exp": False}  # Don't verify expiration for logging
                    )
                    return payload.get("sub", "unknown")
                except Exception:
                    pass
        except Exception:
            pass

        return "anonymous"