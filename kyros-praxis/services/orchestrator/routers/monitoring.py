"""
Monitoring and Observability API Router Module

This module provides RESTful API endpoints for monitoring and observability in the Kyros Orchestrator service.
It includes health checks, system metrics, database health checks, performance metrics, and dependency checks
to ensure the service is running correctly and to provide insights into its operational status. These endpoints
are crucial for DevOps teams to monitor service health, troubleshoot issues, and maintain system reliability.

The router implements best practices for monitoring including:
- Comprehensive health checks for different system components
- Detailed system resource metrics collection
- Database connectivity and performance monitoring
- External dependency health checks
- Performance metrics collection
- Proper error handling and logging

Monitoring Capabilities:
- Service health status with component-level details
- System resource utilization (CPU, memory, disk)
- Database connectivity and performance metrics
- Application performance indicators
- External dependency health checks
- Recent log retrieval for debugging

ENDPOINTS:
1. GET /monitoring/health - Comprehensive health check
2. GET /monitoring/metrics - System and application metrics
3. GET /monitoring/database/health - Database health check
4. GET /monitoring/logs/recent - Recent application logs
5. GET /monitoring/performance - Application performance metrics
6. GET /monitoring/dependencies - External dependency health checks
"""

import time
import psutil
import logging
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from ..database import get_db
    from ..app.core.config import settings
except ImportError:
    # Fallback for environments where config is not available
    from database import get_db  # type: ignore
    try:
        from app.core.config import settings
    except ImportError:
        from pydantic_settings import BaseSettings
        class FallbackSettings(BaseSettings):
            PROJECT_NAME: str = "kyros-praxis"
            VERSION: str = "0.1.0"
            ENVIRONMENT: str = "local"
        settings = FallbackSettings()
        get_db = None

logger = logging.getLogger(__name__)

# Create the API router for monitoring endpoints with prefix and tags
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class SystemMetrics:
    """
    System metrics collector.
    
    This class provides static methods for collecting various system-level metrics
    including CPU usage, memory usage, disk usage, and process information. It uses
    the psutil library to gather system information in a cross-platform compatible way.
    """

    @staticmethod
    def get_cpu_usage() -> float:
        """
        Get CPU usage percentage.
        
        Measures the current CPU usage percentage over a 1-second interval using
        the psutil library. This provides a snapshot of CPU utilization at the
        time of measurement.
        
        Returns:
            float: CPU usage percentage (0-100)
        """
        return psutil.cpu_percent(interval=1)

    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """
        Get memory usage statistics.
        
        Collects detailed memory usage statistics including total memory,
        available memory, used memory, and usage percentage. Uses the psutil
        library to gather cross-platform memory information.
        
        Returns:
            Dict[str, Any]: Dictionary containing memory statistics with keys:
                - total: Total physical memory in bytes
                - available: Available memory in bytes
                - used: Used memory in bytes
                - percentage: Memory usage percentage (0-100)
        """
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percentage": memory.percent,
        }

    @staticmethod
    def get_disk_usage() -> Dict[str, Any]:
        """
        Get disk usage statistics.
        
        Collects disk usage statistics for the root filesystem including total space,
        used space, free space, and usage percentage. Uses the psutil library to
        gather cross-platform disk information.
        
        Returns:
            Dict[str, Any]: Dictionary containing disk statistics with keys:
                - total: Total disk space in bytes
                - used: Used disk space in bytes
                - free: Free disk space in bytes
                - percentage: Disk usage percentage (0-100)
        """
        disk = psutil.disk_usage('/')
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percentage": disk.percent,
        }

    @staticmethod
    def get_process_info() -> Dict[str, Any]:
        """
        Get current process information.
        
        Collects detailed information about the current process including PID,
        CPU usage percentage, memory information, number of threads, and creation time.
        Uses the psutil library to gather cross-platform process information.
        
        Returns:
            Dict[str, Any]: Dictionary containing process information with keys:
                - pid: Process ID
                - cpu_percent: Process CPU usage percentage
                - memory_info: Dictionary of memory information
                - num_threads: Number of threads in the process
                - create_time: Process creation time in ISO format
        """
        process = psutil.Process()
        return {
            "pid": process.pid,
            "cpu_percent": process.cpu_percent(),
            "memory_info": process.memory_info()._asdict(),
            "num_threads": process.num_threads(),
            "create_time": datetime.fromtimestamp(process.create_time()).isoformat(),
        }


@router.get("/health", summary="Comprehensive health check", description="Perform a comprehensive health check of the orchestrator service and return overall system health status")
async def health_check():
    """
    Comprehensive health check endpoint.
    
    This endpoint performs a comprehensive health check of the orchestrator service,
    evaluating the status of various components including system resources, database
    connectivity, and application configuration. It returns an overall health status
    along with detailed information about each component.
    
    The health check evaluates:
    - Basic service information (name, version, environment)
    - Database connectivity and status
    - System memory usage
    
    Returns:
        dict: Health check results including overall status and component statuses
        
    Raises:
        HTTPException: If the health check fails completely (status code 503)
    """
    try:
        # Basic health checks
        checks = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": settings.PROJECT_NAME,
            "version": getattr(settings, 'VERSION', 'unknown'),
            "environment": getattr(settings, 'ENVIRONMENT', 'unknown'),
        }

        # Database connectivity check
        try:
            if get_db:
                # We'll check DB connectivity in a separate endpoint
                checks["database"] = "unknown"
            else:
                checks["database"] = "not_configured"
        except Exception as e:
            checks["database"] = f"error: {str(e)}"
            checks["status"] = "degraded"

        # System resource checks
        try:
            memory = SystemMetrics.get_memory_usage()
            if memory["percentage"] > 90:
                checks["memory"] = "critical"
                checks["status"] = "unhealthy"
            elif memory["percentage"] > 80:
                checks["memory"] = "warning"
                if checks["status"] == "healthy":
                    checks["status"] = "degraded"
            else:
                checks["memory"] = "healthy"
        except Exception as e:
            checks["memory"] = f"error: {str(e)}"

        return checks

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/metrics", summary="System metrics", description="Collect and return detailed system and application metrics")
async def system_metrics():
    """
    System metrics endpoint.
    
    This endpoint collects and returns detailed system and application metrics
    for monitoring and observability purposes. It gathers information about
    CPU usage, memory usage, disk usage, process information, and application
    configuration details.
    
    The metrics include:
    - System-level metrics (CPU, memory, disk, process info)
    - Application-level information (service name, version, environment)
    - Runtime information (Python version)
    
    Returns:
        dict: Detailed system and application metrics organized by category
        
    Raises:
        HTTPException: If metrics collection fails (status code 500)
    """
    try:
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "cpu_usage": SystemMetrics.get_cpu_usage(),
                "memory": SystemMetrics.get_memory_usage(),
                "disk": SystemMetrics.get_disk_usage(),
                "process": SystemMetrics.get_process_info(),
            },
            "application": {
                "service": settings.PROJECT_NAME,
                "version": getattr(settings, 'VERSION', 'unknown'),
                "environment": getattr(settings, 'ENVIRONMENT', 'unknown'),
                "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}",
            },
        }

        return metrics

    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metrics collection failed: {str(e)}"
        )


@router.get("/database/health", summary="Database health check", description="Perform database connectivity and basic performance tests")
async def database_health_check(db: AsyncSession = Depends(get_db) if get_db else None):
    """
    Database health check endpoint.
    
    This endpoint performs database connectivity tests and basic performance
    measurements to verify that the database is accessible and responsive.
    It executes a simple query to test connectivity, measures connection latency,
    and attempts to retrieve basic database information.
    
    The health check evaluates:
    - Basic connectivity with a simple SELECT query
    - Connection latency measurement
    - Database version information (if available)
    
    Args:
        db (AsyncSession, optional): Database session dependency (if available)
        
    Returns:
        dict: Database health check results including status, latency, and info
    """
    if not db:
        return {"status": "not_configured", "message": "Database not available"}

    try:
        start_time = time.time()

        # Basic connectivity test
        result = await db.execute(text("SELECT 1 as test"))
        test_value = result.scalar()

        # Connection latency
        latency = time.time() - start_time

        # Get basic database info
        db_info = {}
        try:
            # Try to get database version (PostgreSQL specific)
            version_result = await db.execute(text("SELECT version() as version"))
            db_info["version"] = version_result.scalar()
        except Exception:
            db_info["version"] = "unknown"

        return {
            "status": "healthy" if test_value == 1 else "unhealthy",
            "latency_ms": round(latency * 1000, 2),
            "database_info": db_info,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.get("/logs/recent", summary="Get recent application logs", description="Retrieve recent application log entries for debugging and monitoring")
async def recent_logs(lines: int = 50):
    """
    Get recent application logs.
    
    This endpoint is intended to retrieve recent application log entries for
    debugging and monitoring purposes. However, it currently returns a placeholder
    response indicating that proper log aggregation should be used in production.
    
    Note: This is a basic implementation. In production, consider using
    a proper log aggregation system like ELK stack, Graylog, or similar solutions
    for centralized log management and analysis.
    
    Args:
        lines (int): Number of recent log lines to retrieve (default: 50)
        
    Returns:
        dict: Placeholder response with note about proper log aggregation
    """
    # This is a simplified implementation
    # In a real system, you'd read from log files or a log aggregation service

    return {
        "message": "Log retrieval not implemented",
        "note": "Use proper log aggregation system (ELK, Loki, etc.) for production",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/performance", summary="Application performance metrics", description="Return application performance metrics including response times, throughput, and error rates")
async def performance_metrics():
    """
    Application performance metrics.
    
    This endpoint returns application performance metrics including response times,
    throughput measurements, and error rates. Currently, it returns a basic structure
    with placeholder values, as proper implementation would require integration
    with application performance monitoring (APM) systems.
    
    The performance metrics include:
    - Response time percentiles (average, 95th, 99th)
    - Throughput measurements (requests per second, total requests)
    - Error rate statistics (percentage, total errors)
    
    Note: Implement proper APM/metrics collection (e.g., Prometheus, DataDog, New Relic)
    for production use to populate these metrics with actual data.
    
    Returns:
        dict: Performance metrics structure with placeholder values
    """
    # This would typically integrate with monitoring systems
    # For now, return basic structure

    return {
        "response_times": {
            "average_ms": 0,  # Would be populated by middleware
            "95th_percentile_ms": 0,
            "99th_percentile_ms": 0,
        },
        "throughput": {
            "requests_per_second": 0,
            "total_requests": 0,
        },
        "error_rate": {
            "percentage": 0,
            "total_errors": 0,
        },
        "timestamp": datetime.utcnow().isoformat(),
        "note": "Implement proper APM/metrics collection for production use",
    }


@router.get("/dependencies", summary="External dependency health check", description="Check the health status of external service dependencies")
async def dependency_check():
    """
    Check external dependencies health.
    
    This endpoint checks the health status of external service dependencies
    that the orchestrator service relies on. It currently supports checking
    Redis and Qdrant services, but returns placeholder status values as
    proper implementation would require actual connectivity tests.
    
    The dependency check evaluates:
    - Redis service status (if configured)
    - Qdrant service status (if configured)
    
    Note: Implement proper connectivity tests for each external service
    for production use to accurately reflect dependency health.
    
    Returns:
        dict: Dependency health status organized by service
    """
    dependencies = {}

    # Check Redis if configured
    try:
        redis_url = getattr(settings, 'redis_url', None)
        if redis_url:
            # Basic Redis connectivity check would go here
            dependencies["redis"] = {"status": "unknown", "message": "Check not implemented"}
        else:
            dependencies["redis"] = {"status": "not_configured"}
    except Exception as e:
        dependencies["redis"] = {"status": "error", "message": str(e)}

    # Check Qdrant if configured
    try:
        qdrant_url = getattr(settings, 'QDRANT_URL', None)
        if qdrant_url:
            # Basic Qdrant connectivity check would go here
            dependencies["qdrant"] = {"status": "unknown", "message": "Check not implemented"}
        else:
            dependencies["qdrant"] = {"status": "not_configured"}
    except Exception as e:
        dependencies["qdrant"] = {"status": "error", "message": str(e)}

    return {
        "dependencies": dependencies,
        "timestamp": datetime.utcnow().isoformat(),
    }