"""
Utility endpoints for the orchestrator service.
"""
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..app.core.config import settings
except ImportError:
    from database import get_db  # type: ignore
    from app.core.config import settings  # type: ignore

router = APIRouter(prefix="/utils", tags=["utils"])


@router.get("/health-check")
def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Comprehensive health check endpoint.
    
    Returns:
        Health status including database connectivity and service information.
    """
    health_status = {
        "status": "healthy",
        "service": "orchestrator",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "unknown",
        "redis": "unknown",
    }
    
    # Check database
    try:
        result = db.execute(text("SELECT 1"))
        result.scalar()
        health_status["database"] = "healthy"
    except Exception as e:
        health_status["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis if configured
    if settings.redis_url:
        try:
            import redis
            r = redis.from_url(settings.redis_url)
            r.ping()
            health_status["redis"] = "healthy"
        except Exception as e:
            health_status["redis"] = f"unhealthy: {str(e)}"
            # Redis is optional, so don't degrade overall status
    
    return health_status


@router.get("/info")
def service_info() -> Dict[str, Any]:
    """
    Get service information.
    
    Returns:
        Service configuration and capabilities.
    """
    return {
        "service": "orchestrator",
        "version": settings.VERSION,
        "project_name": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "api_v1_str": settings.API_V1_STR,
        "cors_origins": settings.all_cors_origins,
        "features": {
            "emails_enabled": settings.emails_enabled,
            "local_password_auth": settings.ENABLE_LOCAL_PASSWORD_AUTH,
            "seed_data": settings.ENABLE_SEED,
        },
    }