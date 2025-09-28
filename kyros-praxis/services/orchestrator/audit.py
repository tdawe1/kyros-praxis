"""
Security audit logging module for Kyros Orchestrator.

This module provides comprehensive audit logging for security events including
authentication attempts, authorization checks, and administrative actions.
It ensures compliance with security standards and enables forensic analysis.

SECURITY AUDIT FEATURES:
-----------------------
1. Authentication Events:
   - Login attempts (successful/failed)
   - Token creation and validation
   - Session management events

2. Authorization Events:
   - Permission checks (granted/denied)
   - Role-based access attempts
   - Privilege escalation attempts

3. Administrative Events:
   - User management operations
   - System configuration changes
   - Security policy updates

4. Data Access Events:
   - Sensitive data access
   - Job and task operations
   - API endpoint access

The audit trail provides:
- Immutable event logging
- Structured event data
- Real-time security monitoring
- Compliance reporting capabilities
"""

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel

try:
    from .app.core.logging import log_orchestrator_event
    from .models import User
except ImportError:
    # Fallback for direct execution
    from app.core.logging import log_orchestrator_event  # type: ignore
    from models import User  # type: ignore


class AuditEventType(str, Enum):
    """Enumeration of security audit event types."""
    
    # Authentication Events
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    TOKEN_CREATED = "auth.token.created"
    TOKEN_VALIDATED = "auth.token.validated"
    TOKEN_EXPIRED = "auth.token.expired"
    
    # Authorization Events
    PERMISSION_GRANTED = "authz.permission.granted"
    PERMISSION_DENIED = "authz.permission.denied"
    ROLE_CHECK_SUCCESS = "authz.role.success"
    ROLE_CHECK_FAILURE = "authz.role.failure"
    
    # Administrative Events
    USER_CREATED = "admin.user.created"
    USER_UPDATED = "admin.user.updated"
    USER_DELETED = "admin.user.deleted"
    ROLE_ASSIGNED = "admin.role.assigned"
    
    # Data Access Events
    JOB_ACCESSED = "data.job.accessed"
    JOB_CREATED = "data.job.created"
    JOB_UPDATED = "data.job.updated"
    JOB_DELETED = "data.job.deleted"
    
    # System Events
    CONFIG_CHANGED = "system.config.changed"
    SECURITY_VIOLATION = "system.security.violation"


class AuditEvent(BaseModel):
    """Model for structured audit events."""
    
    event_type: AuditEventType
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    result: str  # "success" or "failure"
    details: Dict[str, Any] = {}
    timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SecurityAuditor:
    """Central class for security audit logging."""
    
    @staticmethod
    def log_authentication_event(
        event_type: AuditEventType,
        username: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        result: str = "success",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log authentication-related security events.
        
        Args:
            event_type: Type of authentication event
            username: Username involved in the event
            user_id: User ID involved in the event
            ip_address: Client IP address
            user_agent: Client user agent
            result: Event result ("success" or "failure")
            details: Additional event details
        """
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            result=result,
            details=details or {},
            timestamp=datetime.now(timezone.utc)
        )
        
        SecurityAuditor._write_audit_log(event)
    
    @staticmethod
    def log_authorization_event(
        event_type: AuditEventType,
        user: User,
        resource: str,
        action: str,
        result: str,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log authorization-related security events.
        
        Args:
            event_type: Type of authorization event
            user: User object for the event
            resource: Resource being accessed
            action: Action being performed
            result: Event result ("success" or "failure")
            ip_address: Client IP address
            details: Additional event details
        """
        event = AuditEvent(
            event_type=event_type,
            user_id=user.id,
            username=user.username,
            ip_address=ip_address,
            resource=resource,
            action=action,
            result=result,
            details=details or {},
            timestamp=datetime.now(timezone.utc)
        )
        
        SecurityAuditor._write_audit_log(event)
    
    @staticmethod
    def log_data_access_event(
        event_type: AuditEventType,
        user: User,
        resource: str,
        resource_id: str,
        action: str,
        result: str = "success",
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log data access security events.
        
        Args:
            event_type: Type of data access event
            user: User object for the event
            resource: Type of resource accessed (e.g., "job", "task")
            resource_id: ID of the specific resource
            action: Action performed on the resource
            result: Event result ("success" or "failure")
            ip_address: Client IP address
            details: Additional event details
        """
        event_details = details or {}
        event_details.update({
            "resource_id": resource_id,
            "resource_type": resource
        })
        
        event = AuditEvent(
            event_type=event_type,
            user_id=user.id,
            username=user.username,
            ip_address=ip_address,
            resource=resource,
            action=action,
            result=result,
            details=event_details,
            timestamp=datetime.now(timezone.utc)
        )
        
        SecurityAuditor._write_audit_log(event)
    
    @staticmethod
    def log_security_violation(
        violation_type: str,
        user: Optional[User] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log security violations and suspicious activities.
        
        Args:
            violation_type: Type of security violation
            user: User object if available
            ip_address: Client IP address
            details: Additional violation details
        """
        event_details = details or {}
        event_details.update({"violation_type": violation_type})
        
        event = AuditEvent(
            event_type=AuditEventType.SECURITY_VIOLATION,
            user_id=user.id if user else None,
            username=user.username if user else None,
            ip_address=ip_address,
            result="failure",
            details=event_details,
            timestamp=datetime.now(timezone.utc)
        )
        
        SecurityAuditor._write_audit_log(event)
    
    @staticmethod
    def _write_audit_log(event: AuditEvent) -> None:
        """
        Write audit event to the centralized logging system.
        
        Args:
            event: Audit event to log
        """
        # Convert event to dictionary for logging
        log_data = event.dict()
        
        # Use the centralized logging system
        log_orchestrator_event(
            event_type="security_audit",
            user_id=event.user_id,
            data={
                "audit_event": log_data,
                "security_level": "audit",
                "compliance": True
            }
        )


# Convenience functions for common audit events

def audit_login_attempt(username: str, ip_address: str, success: bool, details: Optional[Dict] = None) -> None:
    """Audit a login attempt."""
    event_type = AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILURE
    result = "success" if success else "failure"
    
    SecurityAuditor.log_authentication_event(
        event_type=event_type,
        username=username,
        ip_address=ip_address,
        result=result,
        details=details
    )


def audit_permission_check(user: User, permission: str, granted: bool, resource: str = "", ip_address: str = "") -> None:
    """Audit a permission check."""
    event_type = AuditEventType.PERMISSION_GRANTED if granted else AuditEventType.PERMISSION_DENIED
    result = "success" if granted else "failure"
    
    SecurityAuditor.log_authorization_event(
        event_type=event_type,
        user=user,
        resource=resource,
        action=f"check_permission:{permission}",
        result=result,
        ip_address=ip_address,
        details={"permission": permission}
    )


def audit_job_access(user: User, job_id: str, action: str, ip_address: str = "") -> None:
    """Audit job access events."""
    SecurityAuditor.log_data_access_event(
        event_type=AuditEventType.JOB_ACCESSED,
        user=user,
        resource="job",
        resource_id=job_id,
        action=action,
        ip_address=ip_address
    )


def audit_role_check(user: User, required_role: str, granted: bool, ip_address: str = "") -> None:
    """Audit role-based access checks."""
    event_type = AuditEventType.ROLE_CHECK_SUCCESS if granted else AuditEventType.ROLE_CHECK_FAILURE
    result = "success" if granted else "failure"
    
    SecurityAuditor.log_authorization_event(
        event_type=event_type,
        user=user,
        resource="system",
        action=f"check_role:{required_role}",
        result=result,
        ip_address=ip_address,
        details={"required_role": required_role, "user_role": user.role}
    )