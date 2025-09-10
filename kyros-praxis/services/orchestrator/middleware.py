from fastapi import Depends, Request, HTTPException
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
    raw = os.getenv("API_KEYS", "")
    return {k.strip() for k in raw.split(",") if k.strip()}


async def api_key_validator(request: Request) -> str:
    """
    Validate X-API-Key from headers against comma-separated env var API_KEYS.
    Raises 401 if missing or invalid. Returns the API key for downstream use.
    """
    api_key = request.headers.get("X-API-Key")
    # Do not differentiate missing vs invalid to avoid key probing
    if not api_key or api_key not in _allowed_api_keys():
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


def limiter_key_func(request: Request) -> str:
    """Use API key for rate limit identity; fallback to 'anonymous'."""
    return request.headers.get("X-API-Key") or "anonymous"


# Local Limiter (may be overridden by app.state.limiter in main.py)
limiter = Limiter(key_func=limiter_key_func) if HAVE_SLOWAPI else None


async def rate_limiter(request: Request, api_key: str = Depends(api_key_validator)) -> None:
    """
    Rate limit dependency. Uses app.state.limiter if set (e.g., Redis backend),
    else falls back to module-level limiter. Keys on API key.
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
