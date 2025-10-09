"""
Tests for role-based access control system.

This module tests the hierarchical role-based access control functionality,
ensuring that users with higher privilege roles can access endpoints requiring
lower privilege roles, while maintaining proper security boundaries.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException, status
from services.orchestrator.roles import Role, require_role, require_exact_role
from services.orchestrator.models import User


class TestRole:
    """Test cases for the Role enum and its hierarchy methods."""
    
    def test_role_values(self):
        """Test that role enum values match expected strings."""
        assert Role.USER.value == "user"
        assert Role.MODERATOR.value == "moderator"
        assert Role.ADMIN.value == "admin"
    
    def test_hierarchy_order(self):
        """Test that role hierarchy is correctly ordered."""
        hierarchy = Role.get_hierarchy()
        assert hierarchy == [Role.USER, Role.MODERATOR, Role.ADMIN]
        
        # Verify indices match expected privilege levels
        assert hierarchy.index(Role.USER) == 0      # Lowest privilege
        assert hierarchy.index(Role.MODERATOR) == 1 # Medium privilege  
        assert hierarchy.index(Role.ADMIN) == 2     # Highest privilege
    
    def test_admin_can_access_all_roles(self):
        """Test that admin role can access endpoints requiring any role."""
        assert Role.ADMIN.can_access(Role.USER) is True
        assert Role.ADMIN.can_access(Role.MODERATOR) is True
        assert Role.ADMIN.can_access(Role.ADMIN) is True
    
    def test_moderator_can_access_user_and_self(self):
        """Test that moderator can access user and moderator endpoints."""
        assert Role.MODERATOR.can_access(Role.USER) is True
        assert Role.MODERATOR.can_access(Role.MODERATOR) is True
        assert Role.MODERATOR.can_access(Role.ADMIN) is False
    
    def test_user_can_only_access_user_endpoints(self):
        """Test that user role can only access user-level endpoints."""
        assert Role.USER.can_access(Role.USER) is True
        assert Role.USER.can_access(Role.MODERATOR) is False
        assert Role.USER.can_access(Role.ADMIN) is False
    
    def test_same_role_access(self):
        """Test that roles can access endpoints requiring the same role."""
        assert Role.USER.can_access(Role.USER) is True
        assert Role.MODERATOR.can_access(Role.MODERATOR) is True
        assert Role.ADMIN.can_access(Role.ADMIN) is True


class TestRequireRole:
    """Test cases for the require_role dependency function."""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        user = Mock(spec=User)
        user.id = "test-user-id"
        user.username = "testuser"
        user.email = "test@example.com"
        user.active = 1
        return user
    
    @pytest.mark.asyncio
    async def test_admin_user_can_access_user_endpoint(self, mock_user):
        """Test that admin user can access endpoints requiring user role."""
        mock_user.role = "admin"
        
        # Create dependency for user-level endpoint
        user_dependency = require_role(Role.USER)
        
        # Mock get_current_user to return admin user
        with pytest.MonkeyPatch().context() as m:
            async def mock_get_current_user():
                return mock_user
            
            # Call the dependency function directly
            result = await user_dependency(current_user=mock_user)
            assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_moderator_user_can_access_user_endpoint(self, mock_user):
        """Test that moderator user can access endpoints requiring user role."""
        mock_user.role = "moderator"
        
        user_dependency = require_role(Role.USER)
        result = await user_dependency(current_user=mock_user)
        assert result == mock_user
    
    @pytest.mark.asyncio  
    async def test_user_can_access_user_endpoint(self, mock_user):
        """Test that user can access endpoints requiring user role."""
        mock_user.role = "user"
        
        user_dependency = require_role(Role.USER)
        result = await user_dependency(current_user=mock_user)
        assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_user_cannot_access_moderator_endpoint(self, mock_user):
        """Test that user cannot access endpoints requiring moderator role."""
        mock_user.role = "user"
        
        moderator_dependency = require_role(Role.MODERATOR)
        
        with pytest.raises(HTTPException) as exc_info:
            await moderator_dependency(current_user=mock_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Access denied" in exc_info.value.detail
        assert "Required role: moderator" in exc_info.value.detail
        assert "user role: user" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_user_cannot_access_admin_endpoint(self, mock_user):
        """Test that user cannot access endpoints requiring admin role."""
        mock_user.role = "user"
        
        admin_dependency = require_role(Role.ADMIN)
        
        with pytest.raises(HTTPException) as exc_info:
            await admin_dependency(current_user=mock_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Required role: admin" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_moderator_cannot_access_admin_endpoint(self, mock_user):
        """Test that moderator cannot access endpoints requiring admin role.""" 
        mock_user.role = "moderator"
        
        admin_dependency = require_role(Role.ADMIN)
        
        with pytest.raises(HTTPException) as exc_info:
            await admin_dependency(current_user=mock_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Required role: admin" in exc_info.value.detail
        assert "user role: moderator" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_admin_can_access_admin_endpoint(self, mock_user):
        """Test that admin can access endpoints requiring admin role."""
        mock_user.role = "admin"
        
        admin_dependency = require_role(Role.ADMIN)
        result = await admin_dependency(current_user=mock_user)
        assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_invalid_role_raises_exception(self, mock_user):
        """Test that invalid role in database raises 403 exception."""
        mock_user.role = "invalid_role"
        
        user_dependency = require_role(Role.USER)
        
        with pytest.raises(HTTPException) as exc_info:
            await user_dependency(current_user=mock_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "User has invalid role: invalid_role" in exc_info.value.detail


class TestRequireExactRole:
    """Test cases for the require_exact_role dependency function."""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        user = Mock(spec=User)
        user.id = "test-user-id"
        user.username = "testuser"
        user.email = "test@example.com"
        user.active = 1
        return user
    
    @pytest.mark.asyncio
    async def test_exact_role_match_succeeds(self, mock_user):
        """Test that exact role matching succeeds when roles match."""
        mock_user.role = "moderator"
        
        moderator_dependency = require_exact_role(Role.MODERATOR)
        result = await moderator_dependency(current_user=mock_user)
        assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_admin_cannot_access_moderator_exact_endpoint(self, mock_user):
        """Test that admin cannot access moderator-exact endpoints."""
        mock_user.role = "admin"
        
        moderator_dependency = require_exact_role(Role.MODERATOR)
        
        with pytest.raises(HTTPException) as exc_info:
            await moderator_dependency(current_user=mock_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Required exact role: moderator" in exc_info.value.detail
        assert "user role: admin" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_user_cannot_access_moderator_exact_endpoint(self, mock_user):
        """Test that user cannot access moderator-exact endpoints."""
        mock_user.role = "user"
        
        moderator_dependency = require_exact_role(Role.MODERATOR)
        
        with pytest.raises(HTTPException) as exc_info:
            await moderator_dependency(current_user=mock_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Required exact role: moderator" in exc_info.value.detail
        assert "user role: user" in exc_info.value.detail


class TestRoleHierarchyIntegration:
    """Integration tests for role hierarchy in realistic scenarios."""
    
    @pytest.fixture
    def users(self):
        """Create test users with different roles."""
        user = Mock(spec=User)
        user.role = "user"
        user.username = "regular_user"
        
        moderator = Mock(spec=User)
        moderator.role = "moderator"
        moderator.username = "mod_user"
        
        admin = Mock(spec=User)
        admin.role = "admin"
        admin.username = "admin_user"
        
        return {"user": user, "moderator": moderator, "admin": admin}
    
    @pytest.mark.asyncio
    async def test_user_content_accessibility(self, users):
        """Test that user content is accessible by all role levels."""
        user_endpoint = require_role(Role.USER)
        
        # All users should be able to access user content
        for role_name, user in users.items():
            result = await user_endpoint(current_user=user)
            assert result == user, f"{role_name} should access user content"
    
    @pytest.mark.asyncio
    async def test_moderator_content_accessibility(self, users):
        """Test that moderator content is accessible by moderator and admin only."""
        moderator_endpoint = require_role(Role.MODERATOR)
        
        # User should be denied
        with pytest.raises(HTTPException):
            await moderator_endpoint(current_user=users["user"])
        
        # Moderator should be allowed
        result = await moderator_endpoint(current_user=users["moderator"])
        assert result == users["moderator"]
        
        # Admin should be allowed
        result = await moderator_endpoint(current_user=users["admin"])
        assert result == users["admin"]
    
    @pytest.mark.asyncio
    async def test_admin_content_accessibility(self, users):
        """Test that admin content is accessible by admin only."""
        admin_endpoint = require_role(Role.ADMIN)
        
        # User should be denied
        with pytest.raises(HTTPException):
            await admin_endpoint(current_user=users["user"])
        
        # Moderator should be denied
        with pytest.raises(HTTPException):
            await admin_endpoint(current_user=users["moderator"])
        
        # Admin should be allowed
        result = await admin_endpoint(current_user=users["admin"])
        assert result == users["admin"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])