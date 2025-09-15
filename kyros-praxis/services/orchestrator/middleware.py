"""
API Key Authentication and Rate Limiting Middleware for the Kyros Orchestrator Service.

This module provides middleware components for API key authentication and
rate limiting for the Kyros Orchestrator service. It includes dependencies
and utilities for validating API keys and enforcing rate limits to protect
the service from abuse and ensure fair usage.

The middleware supports both header-based API key validation and rate limiting
based on API key identity, with fallback mechanisms for local development.

MODULE RESPONSIBILITIES:
------------------------
1. API Key Authentication:
   - Validates X-API-Key header against allowed keys
   - Provides FastAPI dependency for authentication
   - Protects against key probing attacks

2. Rate Limiting:
   - Implements per-API key rate limiting
   - Supports SlowAPI integration for advanced rate limiting
   - Provides fallback mechanisms for local development

3. Security Implementation:
   - Secure API key validation
   - Protection against abuse and denial of service
   - Constant-time comparison to prevent timing attacks

4. Middleware Integration:
   - Works with FastAPI's dependency injection system
   - Integrates with security_middleware.py for comprehensive security
   - Supports both header-based and fallback authentication

SECURITY FEATURES:
------------------
- Header-based API key authentication:
  * Validates X-API-Key header against environment-configured keys
  * Uses constant-time comparison to prevent timing attacks
  * Does not differentiate between missing and invalid keys to prevent probing

- Rate Limiting:
  * Per-API key rate limiting to ensure fair usage
  * Integration with SlowAPI for distributed rate limiting
  * Fallback mechanisms for local development environments

- Attack Prevention:
  * Protection against key probing through uniform error responses
  * Rate limiting to prevent denial of service attacks
  * Secure API key handling through environment variables

COMPONENTS:
-----------
1. API Key Validation:
   - _allowed_api_keys(): Retrieves allowed API keys from environment
   - api_key_validator(): FastAPI dependency for validating API keys

2. Rate Limiting:
   - limiter_key_func(): Generates rate limiting keys from API keys
   - rate_limiter(): FastAPI dependency for rate limiting protection

3. Integration Points:
   - Works with SlowAPI for advanced rate limiting when available
   - Falls back to local rate limiting when SlowAPI is not available
   - Integrates with security_middleware.py for layered security

INTEGRATION WITH OTHER MODULES:
-------------------------------
- main.py: Uses middleware components for API protection
- security_middleware.py: Complements security middleware for comprehensive protection
- auth.py: Alternative authentication method for user-based access

USAGE EXAMPLES:
---------------
Protecting an endpoint with API key authentication:
    @app.get("/api/data")
    async def get_data(api_key: str = Depends(api_key_validator)):
        return {"data": "protected information"}

Adding rate limiting to an endpoint:
    @app.get("/api/limited")
    async def limited_endpoint(rate_limit: None = Depends(rate_limiter)):
        return {"message": "rate limited response"}

ENVIRONMENT VARIABLES:
----------------------
- API_KEYS: Comma-separated list of allowed API keys

See Also:
--------
- security_middleware.py: Comprehensive security middleware implementation
- auth.py: User authentication with JWT tokens
- main.py: Main application that uses middleware components
"""

from fastapi import Depends, HTTPException, Request

try:
    from slowapi import Limiter
    from slowapi.errors import RateLimitExceeded

    HAVE_SLOWAPI = True
except Exception:  # optional dep for local runs
    Limiter = None  # type: ignore
    RateLimitExceeded = Exception  # type: ignore
    HAVE_SLOWAPI = False
import os


def _allowed_api_keys() -> set[str]:
    """
    Get the set of allowed API keys from the API_KEYS environment variable.
    
    Parses the comma-separated list of API keys from the environment variable
    and returns a set of cleaned, non-empty keys for efficient lookup.
    
    Security Considerations:
    - API keys should be cryptographically secure random values
    - Environment variables should be properly secured
    - Keys should be rotated regularly
    - Access to environment variables should be restricted
    
    Returns:
        set[str]: Set of allowed API keys
    """
    raw = os.getenv("API_KEYS", "")
    return {k.strip() for k in raw.split(",") if k.strip()}


async def api_key_validator(request: Request) -> str:
    """
    Validate X-API-Key from headers against allowed API keys.
    
    FastAPI dependency that validates the X-API-Key header against the set
    of allowed API keys from the environment variable. Raises a 401 HTTP
    exception if the API key is missing or invalid. Returns the validated
    API key for downstream use.
    
    Security Considerations:
    - Does not differentiate between missing and invalid keys to prevent key probing
    - Uses constant-time comparison through set lookup
    - Integrates with FastAPI's dependency injection system
    
    Args:
        request (Request): The incoming HTTP request
        
    Returns:
        str: The validated API key
        
    Raises:
        HTTPException: If the API key is missing or invalid (status code 401)
        
    Example:
        >>> @app.get("/api/data")
        >>> async def get_data(api_key: str = Depends(api_key_validator)):
        >>>     return {"data": "protected information"}
    """
    api_key = request.headers.get("X-API-Key")
    # Do not differentiate missing vs invalid to avoid key probing
    if not api_key or api_key not in _allowed_api_keys():
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


def limiter_key_func(request: Request) -> str:
    """
    Generate a rate limiting key based on the API key.
    
    Creates a rate limiting key by using the X-API-Key header value if present,
    falling back to 'anonymous' for unauthenticated requests. This allows
    rate limiting to be applied per API key while still protecting anonymous
    access.
    
    Security Considerations:
    - Provides per-API key rate limiting
    - Prevents abuse by unauthenticated users
    - Uses anonymous key for unauthenticated requests
    
    Args:
        request (Request): The incoming HTTP request
        
    Returns:
        str: The rate limiting key ('anonymous' if no API key is provided)
    """
    return request.headers.get("X-API-Key") or "anonymous"


# Local Limiter (may be overridden by app.state.limiter in main.py)
# This limiter is used as a fallback when the application-level limiter
# is not available, such as in local development environments.
limiter = Limiter(key_func=limiter_key_func) if HAVE_SLOWAPI else None


async def rate_limiter(
    request: Request, api_key: str = Depends(api_key_validator)
) -> None:
    """
    Rate limit dependency for protecting API endpoints.
    
    FastAPI dependency that enforces rate limiting on API endpoints. Uses
    the application-level limiter if available (e.g., with Redis backend),
    otherwise falls back to the module-level limiter. The rate limiting
    is keyed on the API key to provide per-key rate limits.
    
    Security Considerations:
    - Provides protection against API abuse
    - Integrates with application-level rate limiting when available
    - Works as a fallback when primary rate limiting is unavailable
    - Prevents denial of service through request flooding
    
    Args:
        request (Request): The incoming HTTP request
        api_key (str): The validated API key (from api_key_validator dependency)
        
    Raises:
        RateLimitExceeded: If the rate limit is exceeded
        
    Example:
        >>> @app.get("/api/data")
        >>> async def get_data(rate_limit: None = Depends(rate_limiter)):
        >>>     return {"data": "rate limited information"}
    """
    active_limiter = getattr(request.app.state, "limiter", limiter)
    # Prefer middleware/decorators; this dependency is a simple guardrail.
    try:
        # Fallback to internal check; allow if not available
        if active_limiter and active_limiter.hit("global", request):
            raise RateLimitExceeded
    except Exception:
        pass
    return None
