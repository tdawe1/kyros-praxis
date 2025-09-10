from fastapi import Depends, Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import os
from typing import Optional


def _allowed_api_keys() -> set[str]:
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
    Rate limit dependency. Uses app.state.limiter if set (e.g., Redis backend),
    else falls back to module-level limiter. Keys on API key.
    """
    active_limiter: Limiter = getattr(request.app.state, "limiter", limiter)
    # Use a generic limit bucket name; policies can be refined per-route later.
    if active_limiter.hit("global", request):
        raise RateLimitExceeded
    return None
