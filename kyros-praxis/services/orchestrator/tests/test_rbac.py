"""
Test cases for Role-Based Access Control (RBAC) implementation.

This module provides comprehensive testing for the RBAC system including:
- Permission-based access control
- Role-based authorization  
- User role validation
- Authorization failure scenarios

The tests ensure that users can only access resources they have
permissions for based on their assigned roles.
"""

import pytest
from fastapi import HTTPException
from services.orchestrator.auth import (
    Permission,
    Role,
    ROLE_PERMISSIONS,
    user_has_permission,
    require_permission,
    require_role
)
from services.orchestrator.models import User
from unittest.mock import Mock


class TestPermissionSystem:
    """Test the core permission system functionality."""
    
    def test_role_permissions_mapping(self):
        """Test that all roles have proper permission mappings."""
        # Verify all roles are mapped
        assert Role.USER in ROLE_PERMISSIONS
        assert Role.MODERATOR in ROLE_PERMISSIONS
        assert Role.ADMIN in ROLE_PERMISSIONS
        
        # Verify admin has all permissions
        admin_perms = ROLE_PERMISSIONS[Role.ADMIN]
        all_perms = set(Permission)
        assert admin_perms == all_perms
        
        # Verify user has minimal permissions
        user_perms = ROLE_PERMISSIONS[Role.USER]
        assert Permission.READ_JOBS in user_perms
        assert Permission.CREATE_JOBS in user_perms
        assert Permission.DELETE_USERS not in user_perms
        assert Permission.ADMIN_SYSTEM not in user_perms
    
    def test_user_permission_checking(self):
        """Test user_has_permission function with different roles."""
        # Create mock users with different roles
        user = Mock()
        user.role = Role.USER.value
        
        moderator = Mock()
        moderator.role = Role.MODERATOR.value
        
        admin = Mock()
        admin.role = Role.ADMIN.value
        
        # Test user permissions
        assert user_has_permission(user, Permission.READ_JOBS)
        assert user_has_permission(user, Permission.CREATE_JOBS)
        assert not user_has_permission(user, Permission.DELETE_JOBS)
        assert not user_has_permission(user, Permission.ADMIN_SYSTEM)
        
        # Test moderator permissions
        assert user_has_permission(moderator, Permission.READ_JOBS)
        assert user_has_permission(moderator, Permission.UPDATE_JOBS)
        assert user_has_permission(moderator, Permission.READ_LOGS)
        assert not user_has_permission(moderator, Permission.DELETE_USERS)
        assert not user_has_permission(moderator, Permission.ADMIN_SYSTEM)
        
        # Test admin permissions
        assert user_has_permission(admin, Permission.READ_JOBS)
        assert user_has_permission(admin, Permission.DELETE_JOBS)
        assert user_has_permission(admin, Permission.DELETE_USERS)
        assert user_has_permission(admin, Permission.ADMIN_SYSTEM)
    
    def test_invalid_role_defaults_to_user(self):
        """Test that invalid roles default to user permissions."""
        user = Mock()
        user.role = "invalid_role"
        
        # Should default to user permissions
        assert user_has_permission(user, Permission.READ_JOBS)
        assert not user_has_permission(user, Permission.ADMIN_SYSTEM)


class TestRoleBasedDecorators:
    """Test the role-based authorization decorators."""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        user = Mock()
        user.role = Role.USER.value
        return user
    
    @pytest.fixture
    def mock_admin(self):
        """Create a mock admin for testing."""
        admin = Mock()
        admin.role = Role.ADMIN.value
        return admin
    
    @pytest.mark.asyncio
    async def test_require_permission_success(self, mock_admin):
        """Test successful permission check."""
        # Create permission checker
        check_perm = require_permission(Permission.ADMIN_SYSTEM)
        
        # This should not raise an exception for admin
        result = await check_perm(mock_admin)
        assert result == mock_admin
    
    @pytest.mark.asyncio
    async def test_require_permission_failure(self, mock_user):
        """Test permission check failure."""
        # Create permission checker for admin-only permission
        check_perm = require_permission(Permission.ADMIN_SYSTEM)
        
        # This should raise HTTPException for regular user
        with pytest.raises(HTTPException) as exc_info:
            await check_perm(mock_user)
        
        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in exc_info.value.detail
        assert "system:admin" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_require_role_success(self, mock_admin):
        """Test successful role check."""
        # Create role checker for admin
        check_role = require_role(Role.ADMIN)
        
        # This should not raise an exception
        result = await check_role(mock_admin)
        assert result == mock_admin
    
    @pytest.mark.asyncio
    async def test_require_role_failure(self, mock_user):
        """Test role check failure."""
        # Create role checker for admin role
        check_role = require_role(Role.ADMIN)
        
        # This should raise HTTPException for regular user
        with pytest.raises(HTTPException) as exc_info:
            await check_role(mock_user)
        
        assert exc_info.value.status_code == 403
        assert "Insufficient role" in exc_info.value.detail
        assert "admin" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_admin_bypasses_role_check(self, mock_admin):
        """Test that admin role bypasses other role requirements."""
        # Create role checker for moderator
        check_role = require_role(Role.MODERATOR)
        
        # Admin should bypass this check
        result = await check_role(mock_admin)
        assert result == mock_admin


class TestRBACIntegration:
    """Integration tests for the complete RBAC system."""
    
    def test_permission_hierarchy(self):
        """Test that permission hierarchy works as expected."""
        # User permissions should be subset of moderator
        user_perms = ROLE_PERMISSIONS[Role.USER]
        moderator_perms = ROLE_PERMISSIONS[Role.MODERATOR]
        admin_perms = ROLE_PERMISSIONS[Role.ADMIN]
        
        # User permissions should be included in moderator permissions
        assert user_perms.issubset(moderator_perms)
        
        # Moderator permissions should be included in admin permissions
        assert moderator_perms.issubset(admin_perms)
    
    def test_job_management_permissions(self):
        """Test job-specific permission assignments."""
        user = Mock()
        user.role = Role.USER.value
        
        moderator = Mock()
        moderator.role = Role.MODERATOR.value
        
        admin = Mock()
        admin.role = Role.ADMIN.value
        
        # Users can read and create jobs
        assert user_has_permission(user, Permission.READ_JOBS)
        assert user_has_permission(user, Permission.CREATE_JOBS)
        assert not user_has_permission(user, Permission.UPDATE_JOBS)
        assert not user_has_permission(user, Permission.DELETE_JOBS)
        
        # Moderators can read, create, and update jobs
        assert user_has_permission(moderator, Permission.READ_JOBS)
        assert user_has_permission(moderator, Permission.CREATE_JOBS)
        assert user_has_permission(moderator, Permission.UPDATE_JOBS)
        assert not user_has_permission(moderator, Permission.DELETE_JOBS)
        
        # Admins can do everything with jobs
        assert user_has_permission(admin, Permission.READ_JOBS)
        assert user_has_permission(admin, Permission.CREATE_JOBS)
        assert user_has_permission(admin, Permission.UPDATE_JOBS)
        assert user_has_permission(admin, Permission.DELETE_JOBS)
    
    def test_user_management_permissions(self):
        """Test user management permission assignments."""
        user = Mock()
        user.role = Role.USER.value
        
        moderator = Mock()
        moderator.role = Role.MODERATOR.value
        
        admin = Mock()
        admin.role = Role.ADMIN.value
        
        # Regular users cannot manage other users
        assert not user_has_permission(user, Permission.READ_USERS)
        assert not user_has_permission(user, Permission.CREATE_USERS)
        assert not user_has_permission(user, Permission.UPDATE_USERS)
        assert not user_has_permission(user, Permission.DELETE_USERS)
        
        # Moderators can only read users
        assert user_has_permission(moderator, Permission.READ_USERS)
        assert not user_has_permission(moderator, Permission.CREATE_USERS)
        assert not user_has_permission(moderator, Permission.UPDATE_USERS)
        assert not user_has_permission(moderator, Permission.DELETE_USERS)
        
        # Admins can fully manage users
        assert user_has_permission(admin, Permission.READ_USERS)
        assert user_has_permission(admin, Permission.CREATE_USERS)
        assert user_has_permission(admin, Permission.UPDATE_USERS)
        assert user_has_permission(admin, Permission.DELETE_USERS)


if __name__ == "__main__":
    pytest.main([__file__])