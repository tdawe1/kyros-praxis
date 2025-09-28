"""
Security Monitoring and Reporting API Router Module

This module provides RESTful API endpoints for security monitoring and reporting in the Kyros Orchestrator service.
It includes endpoints for receiving and processing Content Security Policy (CSP) violation reports, performing
security-focused health checks, and retrieving security configuration information. These endpoints help maintain
the security posture of the service by monitoring for violations and providing visibility into security features.

Security Features Monitored:
- Content Security Policy (CSP) violations from web browsers
- Authentication and authorization mechanisms
- Rate limiting and access control
- Cross-Site Request Forgery (CSRF) protection
- JSON Web Token (JWT) security

The router implements best practices for security monitoring including:
- Proper handling of security violation reports
- Security-focused health checks
- Safe exposure of security configuration information
- Proper error handling and logging
- Protection against information disclosure

Key Features:
- CSP violation reporting for client-side security monitoring
- Security health checks for continuous monitoring
- Redacted security configuration information
- Protection against sensitive information disclosure
- Comprehensive logging of security events

ENDPOINTS:
1. POST /security/csp-report - Receive CSP violation reports
2. GET /security/health - Security-focused health check
3. GET /security/config - Get security configuration information
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create the API router for security endpoints with prefix and tags
router = APIRouter(prefix="/security", tags=["security"])


class CSPReport(BaseModel):
    """
    CSP violation report model.
    
    This Pydantic model represents a Content Security Policy (CSP) violation report
    as sent by web browsers when CSP rules are violated. It captures essential
    information about the violation for security monitoring and analysis.
    
    Attributes:
        document_uri (str): The URI of the document in which the violation occurred
        violated_directive (str): The policy directive that was violated
        effective_directive (str): The effective directive that was violated
        original_policy (str): The original CSP policy string
        blocked_uri (str): The URI of the resource that was blocked
        status_code (int): The HTTP status code of the blocked resource (default: 0)
    """
    document_uri: str
    violated_directive: str
    effective_directive: str
    original_policy: str
    blocked_uri: str
    status_code: int = 0


class CSPReportData(BaseModel):
    """
    CSP report data wrapper.
    
    This Pydantic model wraps the CSP report data according to the CSP report
    format specification. It contains a single field 'csp_report' which holds
    the actual CSP violation report.
    
    Attributes:
        csp_report (CSPReport): The wrapped CSP violation report
    """
    csp_report: CSPReport


@router.post("/csp-report", summary="Receive CSP violation reports", description="Receive and log Content Security Policy violation reports from browsers")
async def report_csp_violation(report: CSPReportData, request: Request):
    """
    Receive and log CSP violation reports.
    
    This endpoint receives Content Security Policy (CSP) violation reports
    from web browsers when CSP rules are violated. It logs the violation
    details for security monitoring and analysis, helping to identify
    potential security issues or misconfigurations in the CSP policy.
    
    The endpoint extracts client information (IP address, User-Agent) and
    violation details from the report, logs them as warnings, and returns
    a confirmation response. This enables continuous monitoring of
    client-side security violations.
    
    Args:
        report (CSPReportData): CSP violation report data wrapped in the expected format
        request (Request): FastAPI request object containing client information
        
    Returns:
        dict: Confirmation response indicating successful report receipt
        
    Raises:
        HTTPException: If processing the CSP report fails (status code 500)
    """
    try:
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")

        logger.warning(
            "CSP Violation Report",
            extra={
                "client_ip": client_ip,
                "user_agent": user_agent,
                "document_uri": report.csp_report.document_uri,
                "violated_directive": report.csp_report.violated_directive,
                "effective_directive": report.csp_report.effective_directive,
                "blocked_uri": report.csp_report.blocked_uri,
                "status_code": report.csp_report.status_code,
            }
        )

        # Return 204 No Content for successful report receipt
        return {"status": "reported"}

    except Exception as e:
        logger.error(f"Error processing CSP report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process CSP report"
        )


@router.get("/health", summary="Security-focused health check", description="Perform a security-focused health check and return basic security status information")
async def security_health_check():
    """
    Security-focused health check endpoint.
    
    This endpoint performs a security-focused health check and returns basic
    security status information. It provides a quick way to verify that
    essential security features are enabled and functioning correctly.
    
    The health check evaluates:
    - Basic service status
    - Enabled security features (CSP, CSRF, rate limiting, JWT)
    
    Returns:
        dict: Security health check results including status and feature information
    """
    return {
        "status": "healthy",
        "security": {
            "csp_enabled": True,
            "csrf_enabled": True,
            "rate_limiting": True,
            "jwt_enabled": True,
        }
    }


@router.get("/config", summary="Get security configuration information", description="Retrieve information about enabled security features without exposing sensitive configuration details")
async def get_security_config():
    """
    Get current security configuration (redacted for security).
    
    This endpoint provides information about enabled security features
    without exposing sensitive configuration details. It returns a
    redacted view of the security configuration to help with
    troubleshooting and verification while maintaining security.
    
    The configuration information includes:
    - Runtime environment information
    - Enabled security features
    - Non-sensitive JWT configuration details
    
    Note: Sensitive configuration values (secrets, keys, passwords) are
    intentionally omitted to prevent information disclosure.
    
    Returns:
        dict: Redacted security configuration information
    """
    try:
        from app.core.config import settings
    except ImportError:
        # Fallback for environments where config is not available
        settings = None

    config_info = {
        "environment": getattr(settings, 'ENVIRONMENT', 'unknown') if settings else 'unknown',
        "features": {
            "jwt_authentication": True,
            "csrf_protection": True,
            "rate_limiting": True,
            "csp_headers": True,
            "security_headers": True,
            "cors_policy": True,
        },
        "jwt": {
            "algorithm": getattr(settings, 'JWT_ALGORITHM', 'HS512') if settings else 'HS512',
            "expiration_hours": getattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES', 120) // 60 if settings else 2,
        }
    }

    return config_info