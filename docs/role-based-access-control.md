# Hierarchical Role-Based Access Control

This document describes the hierarchical role-based access control system that resolves the issue "Denying elevated roles in role-based dependency" where elevated roles (moderator, admin) were incorrectly denied access to endpoints requiring lower roles (user).

## Issue Resolution

**Original Problem:** The `require_role` dependency was only granting access when the user's role exactly matched the required role OR when the user was an admin. This meant higher roles (e.g., moderator) were blocked from endpoints that required lower roles (e.g., `Role.USER`), breaking the hierarchical role model.

**Solution Implemented:** The system now uses a proper hierarchical role-based access control where higher privilege roles can access endpoints that require lower privilege roles, while maintaining strict security boundaries.

## Overview

The role-based access control system now supports hierarchical permissions, where users with higher privilege roles can access endpoints that require lower privilege roles. This maintains security while providing the expected role model behavior.

## Role Hierarchy

The system defines three roles in order of increasing privilege:

1. **USER** - Basic user permissions
2. **MODERATOR** - Elevated permissions, can access user endpoints  
3. **ADMIN** - Full system access, can access any endpoint

## Access Rules

- **Higher privilege roles inherit lower role permissions**
- **Same privilege level has access**
- **Lower privilege roles cannot access higher level endpoints**

### Access Matrix

| User Role | Can Access USER | Can Access MODERATOR | Can Access ADMIN |
|-----------|----------------|---------------------|------------------|
| USER      | ✅ Yes         | ❌ No               | ❌ No            |
| MODERATOR | ✅ Yes         | ✅ Yes              | ❌ No            |
| ADMIN     | ✅ Yes         | ✅ Yes              | ✅ Yes           |

## Usage

### Basic Role Dependencies

Use `require_role()` for hierarchical access control:

```python
from services.orchestrator.roles import Role, require_role
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/user-content")
async def get_user_content(current_user: User = Depends(require_role(Role.USER))):
    """Accessible by user, moderator, and admin roles."""
    return {"message": "User content", "user_role": current_user.role}

@router.get("/moderator-content") 
async def get_moderator_content(current_user: User = Depends(require_role(Role.MODERATOR))):
    """Accessible by moderator and admin roles only."""
    return {"message": "Moderator content", "user_role": current_user.role}

@router.get("/admin-content")
async def get_admin_content(current_user: User = Depends(require_role(Role.ADMIN))):
    """Accessible by admin role only."""
    return {"message": "Admin content", "user_role": current_user.role}
```

### Exact Role Matching

Use `require_exact_role()` when you need functionality specific to one role only:

```python
from services.orchestrator.roles import require_exact_role

@router.get("/moderator-tools")
async def get_moderator_tools(current_user: User = Depends(require_exact_role(Role.MODERATOR))):
    """Accessible by moderator role only (not admin)."""
    return {"tools": ["moderation_queue", "user_reports"]}
```

## Migration from Old System

If you have existing code using the old role checking pattern, update as follows:

### Before (Problematic)
```python
# This would deny moderators access to user endpoints
@router.get("/endpoint")
async def endpoint(current_user: User = Depends(get_current_user)):
    if current_user.role != "user":
        raise HTTPException(status_code=403, detail="Access denied")
    return {"data": "user content"}
```

### After (Fixed)
```python
# This allows moderators and admins to access user endpoints
@router.get("/endpoint")
async def endpoint(current_user: User = Depends(require_role(Role.USER))):
    return {"data": "user content"}
```

## Testing the Role System

### Unit Tests

The system includes comprehensive unit tests:

```bash
# Run role-specific tests
pytest services/orchestrator/tests/unit/test_roles.py -v

# Run integration tests
pytest services/orchestrator/tests/test_role_integration.py -v
```

### Example Endpoints

Try the example endpoints to see the role system in action:

```bash
# Start the orchestrator service
uvicorn services.orchestrator.main:app --reload

# Test with different user roles
curl -H "Authorization: Bearer <user_token>" http://localhost:8000/api/v1/examples/user-content
curl -H "Authorization: Bearer <moderator_token>" http://localhost:8000/api/v1/examples/user-content
curl -H "Authorization: Bearer <admin_token>" http://localhost:8000/api/v1/examples/user-content
```

## API Documentation

The FastAPI documentation automatically includes role information:

- Visit `http://localhost:8000/docs` to see the interactive API documentation
- Each endpoint shows which roles can access it
- The role examples under the "role-examples" tag demonstrate the hierarchy

## Security Considerations

### What Changed
- **Fixed**: Moderators can now access user-level endpoints
- **Fixed**: Admins can now access user and moderator-level endpoints
- **Maintained**: Users still cannot access moderator or admin endpoints
- **Maintained**: Moderators still cannot access admin endpoints

### What Didn't Change
- Authentication is still required for all protected endpoints
- JWT token validation remains the same
- User model and database schema unchanged
- Existing admin-only functionality preserved

## Troubleshooting

### Common Issues

1. **403 Forbidden with valid token**
   - Check that user role is correctly set in database
   - Verify role value matches enum: "user", "moderator", or "admin"

2. **Invalid role error**
   - User has a role not defined in the Role enum
   - Update user role to valid value or add new role to enum

3. **Import errors**
   - Ensure `from services.orchestrator.roles import Role, require_role`
   - Check that FastAPI and dependencies are installed

### Debugging

Check user role information:

```python
@router.get("/debug/role-info")
async def debug_role_info(current_user: User = Depends(require_role(Role.USER))):
    user_role = Role(current_user.role)
    return {
        "username": current_user.username,
        "role": current_user.role,
        "can_access_user": user_role.can_access(Role.USER),
        "can_access_moderator": user_role.can_access(Role.MODERATOR),
        "can_access_admin": user_role.can_access(Role.ADMIN)
    }
```

## Original Issue Resolution

**Issue**: `require_role(Role.USER)` would reject moderators with a 403 error despite them being more privileged.

**Root Cause**: The system only allowed exact role matches, breaking the stated role hierarchy.

**Solution**: Implemented `can_access()` method that compares role privilege levels, allowing higher roles to access lower-privilege endpoints.

**Verification**: 
- ✅ Moderators can now access user endpoints
- ✅ Admins can now access user and moderator endpoints  
- ✅ Security boundaries maintained for lower→higher access
- ✅ Existing admin functionality preserved