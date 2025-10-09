"""
Role-based access control module for the Kyros Orchestrator service.

This module provides hierarchical role-based access control functionality,
allowing users with higher privilege roles to access endpoints that require
lower privilege roles, while maintaining strict access control for admin-only
functions.

Role Hierarchy:
- admin: Full system access, can access any endpoint
- moderator: Elevated permissions, can access user endpoints
- user: Basic user permissions

USAGE EXAMPLE:
--------------
@app.get("/user-endpoint")
async def user_endpoint(current_user: User = Depends(require_role(Role.USER))):
    # Accessible by user, moderator, and admin roles
    return {"message": "User content"}

@app.get("/admin-endpoint")  
async def admin_endpoint(current_user: User = Depends(require_role(Role.ADMIN))):
    # Accessible only by admin role
    return {"message": "Admin content"}
"""

from enum import Enum
from typing import Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from .auth import get_current_user
    from .models import User
except ImportError:
    try:
        # Fallback for when running as standalone module
        from auth import get_current_user  # type: ignore
        from models import User  # type: ignore
    except ImportError:
        # For testing, we'll create mock imports
        get_current_user = None
        User = None


class Role(Enum):
    """
    User role enumeration with hierarchical ordering.
    
    Roles are ordered from lowest to highest privilege level.
    Higher privilege roles can access endpoints that require lower privilege roles.
    
    Hierarchy (lowest to highest):
    - USER: Basic user permissions
    - MODERATOR: Elevated permissions, can access user endpoints
    - ADMIN: Full system access, can access any endpoint
    """
    USER = "user"
    MODERATOR = "moderator" 
    ADMIN = "admin"
    
    @classmethod
    def get_hierarchy(cls) -> list["Role"]:
        """
        Get role hierarchy from lowest to highest privilege.
        
        Returns:
            list[Role]: Ordered list of roles from lowest to highest privilege
        """
        return [cls.USER, cls.MODERATOR, cls.ADMIN]
    
    def can_access(self, required_role: "Role") -> bool:
        """
        Check if this role can access an endpoint requiring the specified role.
        
        Higher privilege roles can access endpoints that require lower privilege roles.
        
        Args:
            required_role (Role): The minimum role required for access
            
        Returns:
            bool: True if this role can access the endpoint, False otherwise
            
        Examples:
            >>> Role.ADMIN.can_access(Role.USER)
            True
            >>> Role.USER.can_access(Role.ADMIN)  
            False
            >>> Role.MODERATOR.can_access(Role.USER)
            True
        """
        hierarchy = self.get_hierarchy()
        current_level = hierarchy.index(self)
        required_level = hierarchy.index(required_role)
        
        # Higher or equal privilege level can access
        return current_level >= required_level


def require_role(required_role: Role) -> Callable:
    """
    FastAPI dependency factory for role-based access control.
    
    Creates a dependency that enforces role-based access control with hierarchical
    permissions. Users with higher privilege roles can access endpoints that
    require lower privilege roles.
    
    Args:
        required_role (Role): Minimum role required for access
        
    Returns:
        Callable: FastAPI dependency function that validates user role
        
    Raises:
        HTTPException: 403 Forbidden if user doesn't have sufficient privileges
        
    Examples:
        @app.get("/user-content")
        async def get_user_content(user: User = Depends(require_role(Role.USER))):
            # Accessible by user, moderator, and admin
            return {"data": "user content"}
            
        @app.get("/admin-panel")  
        async def get_admin_panel(user: User = Depends(require_role(Role.ADMIN))):
            # Accessible only by admin
            return {"data": "admin panel"}
    """
    async def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        """
        Validate that the current user has sufficient role privileges.
        
        Args:
            current_user (User): Authenticated user from JWT token
            
        Returns:
            User: The authenticated user if role check passes
            
        Raises:
            HTTPException: 403 Forbidden if user doesn't have sufficient privileges
        """
        try:
            user_role = Role(current_user.role)
        except ValueError:
            # Invalid role in database
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User has invalid role: {current_user.role}"
            )
        
        if not user_role.can_access(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role.value}, user role: {user_role.value}"
            )
        
        return current_user
    
    return role_dependency


def require_exact_role(required_role: Role) -> Callable:
    """
    FastAPI dependency factory for exact role matching.
    
    Creates a dependency that requires the user to have exactly the specified role.
    Unlike require_role(), this does not allow higher privilege roles to access
    the endpoint. This is useful for role-specific functionality.
    
    Args:
        required_role (Role): Exact role required for access
        
    Returns:
        Callable: FastAPI dependency function that validates exact user role
        
    Raises:
        HTTPException: 403 Forbidden if user doesn't have the exact role
        
    Example:
        @app.get("/moderator-tools")
        async def get_moderator_tools(user: User = Depends(require_exact_role(Role.MODERATOR))):
            # Accessible only by moderator role (not admin)
            return {"data": "moderator tools"}
    """
    async def exact_role_dependency(current_user: User = Depends(get_current_user)) -> User:
        """
        Validate that the current user has exactly the required role.
        
        Args:
            current_user (User): Authenticated user from JWT token
            
        Returns:
            User: The authenticated user if role check passes
            
        Raises:
            HTTPException: 403 Forbidden if user doesn't have the exact role
        """
        if current_user.role != required_role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required exact role: {required_role.value}, user role: {current_user.role}"
            )
        
        return current_user
    
    return exact_role_dependency