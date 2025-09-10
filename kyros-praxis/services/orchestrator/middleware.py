from fastapi import Depends, Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import os
from typing import Optional


def _allowed_api_keys() -> set[str]:
    """
    Return the set of allowed API keys parsed from the API_KEYS environment variable.
    
    Reads the environment variable "API_KEYS", splits its value on commas, trims whitespace from each entry, and returns a set of non-empty keys. If API_KEYS is unset or contains only empty/whitespace entries, an empty set is returned.
    """
    raw = os.getenv("API_KEYS", "")
    return {k.strip() for k in raw.split(",") if k.strip()}


async def api_key_validator(request: Request) -> str:
    """
    Validate X-API-Key from headers against comma-separated env var API_KEYS.
    Raises 401 if missing or invalid. Returns the API key for downstream use.
    """
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    if api_key not in _allowed_api_keys():
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


def limiter_key_func(request: Request) -> str:
    """Use API key for rate limit identity; fallback to 'anonymous'."""
    return request.headers.get("X-API-Key") or "anonymous"


# Local Limiter (may be overridden by app.state.limiter in main.py)
limiter = Limiter(key_func=limiter_key_func)


async def rate_limiter(request: Request, api_key: str = Depends(api_key_validator)) -> None:
    """
    Enforce per-key rate limiting for incoming requests.
    
    This async dependency validates rate limits using the application's active limiter (request.app.state.limiter) or the module-level fallback. It is intended to run after api_key_validator (via the dependency injection) so limits are applied per API key; when no API key is present the limiter's key function may treat the request as "anonymous". Uses the generic "global" bucket for checks.
    
    Raises:
    	RateLimitExceeded: if the limiter reports the "global" bucket is over the allowed limit.
    """
    active_limiter: Limiter = getattr(request.app.state, "limiter", limiter)
    # Use a generic limit bucket name; policies can be refined per-route later.
    if active_limiter.hit("global", request):
        raise RateLimitExceeded
    return None
