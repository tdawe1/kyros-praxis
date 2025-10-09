"""
Example router demonstrating hierarchical role-based access control.

This router provides example endpoints that demonstrate how to use the
hierarchical role system, showing how different role levels can access
different endpoints based on their privilege level.
"""

from fastapi import APIRouter, Depends
from services.orchestrator.roles import Role, require_role, require_exact_role
from services.orchestrator.models import User

router = APIRouter(prefix="/examples", tags=["role-examples"])


@router.get("/user-content", summary="User content endpoint", description="Content accessible by any authenticated user")
async def get_user_content(current_user: User = Depends(require_role(Role.USER))):
    """
    Example endpoint accessible by user, moderator, and admin roles.
    
    This demonstrates the hierarchical nature of the role system where
    higher privilege roles (moderator, admin) can access endpoints that
    require lower privilege roles (user).
    
    Args:
        current_user (User): Authenticated user (user, moderator, or admin)
        
    Returns:
        dict: User content data
    """
    return {
        "message": "User content accessible to all authenticated users",
        "content_type": "user",
        "user": {
            "username": current_user.username,
            "role": current_user.role
        },
        "access_note": "This endpoint is accessible by user, moderator, and admin roles"
    }


@router.get("/moderator-content", summary="Moderator content endpoint", description="Content accessible by moderator and admin roles")
async def get_moderator_content(current_user: User = Depends(require_role(Role.MODERATOR))):
    """
    Example endpoint accessible by moderator and admin roles only.
    
    This demonstrates how moderator-level content blocks user role access
    but allows admin role access due to hierarchy.
    
    Args:
        current_user (User): Authenticated user (moderator or admin only)
        
    Returns:
        dict: Moderator content data
    """
    return {
        "message": "Moderator content with elevated permissions",
        "content_type": "moderator",
        "user": {
            "username": current_user.username,
            "role": current_user.role
        },
        "access_note": "This endpoint is accessible by moderator and admin roles only"
    }


@router.get("/admin-content", summary="Admin content endpoint", description="Content accessible by admin role only")
async def get_admin_content(current_user: User = Depends(require_role(Role.ADMIN))):
    """
    Example endpoint accessible by admin role only.
    
    This demonstrates the highest level of access control where only
    admin users can access sensitive administrative content.
    
    Args:
        current_user (User): Authenticated user (admin only)
        
    Returns:
        dict: Admin content data
    """
    return {
        "message": "Admin content with full system access",
        "content_type": "admin",
        "user": {
            "username": current_user.username,
            "role": current_user.role
        },
        "access_note": "This endpoint is accessible by admin role only"
    }


@router.get("/moderator-tools", summary="Moderator-specific tools", description="Tools available only to moderators (not admins)")
async def get_moderator_tools(current_user: User = Depends(require_exact_role(Role.MODERATOR))):
    """
    Example endpoint using exact role matching for moderator-specific functionality.
    
    This demonstrates the use of require_exact_role() for functionality that
    should only be available to a specific role, not higher privilege roles.
    This might be used for role-specific tools or dashboards.
    
    Args:
        current_user (User): Authenticated user (moderator only, not admin)
        
    Returns:
        dict: Moderator-specific tools data
    """
    return {
        "message": "Moderator-specific tools and functionality",
        "content_type": "moderator-exact",
        "user": {
            "username": current_user.username,
            "role": current_user.role
        },
        "tools": [
            "User management dashboard",
            "Content moderation queue",
            "Report review system"
        ],
        "access_note": "This endpoint is accessible by moderator role only (exact match)"
    }


@router.get("/role-info", summary="User role information", description="Get information about the current user's role and permissions")
async def get_role_info(current_user: User = Depends(require_role(Role.USER))):
    """
    Example endpoint that shows the current user's role and what they can access.
    
    This demonstrates how to provide users with information about their
    current permissions and access levels.
    
    Args:
        current_user (User): Authenticated user (any role)
        
    Returns:
        dict: Role information and accessible endpoints
    """
    user_role = Role(current_user.role)
    
    # Determine which example endpoints this user can access
    accessible_endpoints = []
    
    if user_role.can_access(Role.USER):
        accessible_endpoints.append("user-content")
    
    if user_role.can_access(Role.MODERATOR):
        accessible_endpoints.append("moderator-content")
    
    if user_role.can_access(Role.ADMIN):
        accessible_endpoints.append("admin-content")
    
    # Check exact role access
    exact_access = []
    if current_user.role == Role.MODERATOR.value:
        exact_access.append("moderator-tools")
    
    return {
        "user": {
            "username": current_user.username,
            "role": current_user.role
        },
        "role_hierarchy": {
            "current_level": Role.get_hierarchy().index(user_role),
            "total_levels": len(Role.get_hierarchy()),
            "role_order": [role.value for role in Role.get_hierarchy()]
        },
        "accessible_endpoints": accessible_endpoints,
        "exact_role_endpoints": exact_access,
        "permissions": {
            "can_access_user_content": user_role.can_access(Role.USER),
            "can_access_moderator_content": user_role.can_access(Role.MODERATOR),
            "can_access_admin_content": user_role.can_access(Role.ADMIN)
        }
    }