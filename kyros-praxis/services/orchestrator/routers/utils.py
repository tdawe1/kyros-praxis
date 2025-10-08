"""
Utility Endpoints API Router Module

This module provides utility RESTful API endpoints for the Kyros Orchestrator service.
It includes endpoints for health checking and retrieving service information, which
are useful for monitoring, debugging, and service discovery purposes. These utility
endpoints are essential for DevOps operations, service maintenance, and system administration.

The router implements best practices for utility endpoints including:
- Proper error handling
- Database connectivity verification
- External service health checking
- Safe exposure of service information
- Comprehensive status reporting

Utility Functions:
- Service health verification with database and external service checks
- Service information retrieval for configuration and debugging
- Environment-specific details for troubleshooting
- Feature flag status for capability discovery
- System status reporting for monitoring dashboards

ENDPOINTS:
1. GET /utils/health-check - Comprehensive health check with database and Redis verification
2. GET /utils/info - Service information and configuration details
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..app.core.config import settings
except ImportError:
    from ..database import get_db  # type: ignore
    from app.core.config import settings  # type: ignore

# Create the API router for utility endpoints with prefix and tags
router = APIRouter(prefix="/utils", tags=["utils"])


@router.get("/health-check", summary="Comprehensive health check", description="Perform a comprehensive health check including database connectivity and service information")
def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Comprehensive health check endpoint.
    
    This endpoint performs a comprehensive health check of the orchestrator service,
    including database connectivity verification and optional Redis service checking.
    It returns detailed status information about the service's operational state and
    dependencies.
    
    The health check evaluates:
    - Basic service information (name, version, environment)
    - Database connectivity status
    - Redis service status (if configured)
    
    Args:
        db (Session): Database session dependency for connectivity testing
        
    Returns:
        Dict[str, Any]: Health status information including service details,
                       database status, and Redis status (if configured)
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


@router.get("/info", summary="Get service information", description="Retrieve service configuration and capabilities information")
def service_info() -> Dict[str, Any]:
    """
    Get service information.
    
    This endpoint returns detailed information about the orchestrator service
    including configuration details, version information, and enabled features.
    It's useful for service discovery, debugging, and monitoring purposes.
    
    The information includes:
    - Service identification and version
    - Project configuration details
    - API configuration (version, CORS origins)
    - Enabled feature flags
    
    Returns:
        Dict[str, Any]: Service configuration and capabilities information
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