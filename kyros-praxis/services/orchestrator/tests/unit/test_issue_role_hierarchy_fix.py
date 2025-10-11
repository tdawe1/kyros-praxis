"""
Test suite specifically validating the fix for the role hierarchy issue.

This test validates that the original issue has been resolved:
"Denying elevated roles in role-based dependency"

Original problem: 
- require_role dependency only granted access when user's role exactly matched 
  the required role OR when user was admin
- Higher roles (moderator) were blocked from endpoints requiring lower roles (user)
- This broke the hierarchical role model

Expected fix:
- Higher privilege roles can access endpoints requiring lower privilege roles
- Role hierarchy: USER < MODERATOR < ADMIN
- Security boundaries maintained (lower roles cannot access higher endpoints)
"""

import pytest
from unittest.mock import Mock
from fastapi import HTTPException, status
from services.orchestrator.roles import Role, require_role
from services.orchestrator.models import User


class TestRoleHierarchyIssueFix:
    """Test cases specifically for the role hierarchy issue fix."""
    
    @pytest.fixture
    def mock_users(self):
        """Create mock users for different roles."""
        user = Mock(spec=User)
        user.role = "user"
        user.username = "test_user"
        user.id = "user_id"
        
        moderator = Mock(spec=User)
        moderator.role = "moderator"
        moderator.username = "test_moderator"
        moderator.id = "moderator_id"
        
        admin = Mock(spec=User)
        admin.role = "admin"
        admin.username = "test_admin"
        admin.id = "admin_id"
        
        return {"user": user, "moderator": moderator, "admin": admin}

    @pytest.mark.asyncio
    async def test_original_issue_moderator_denied_user_endpoint_is_fixed(self, mock_users):
        """
        Test that the original issue is fixed: moderators can now access user endpoints.
        
        Original issue: require_role(Role.USER) would reject moderators with 403
        Expected fix: moderators should be able to access user endpoints
        """
        user_endpoint_dependency = require_role(Role.USER)
        
        # Moderator should be able to access user endpoint (this was the original issue)
        result = await user_endpoint_dependency(current_user=mock_users["moderator"])
        assert result == mock_users["moderator"], "Moderator should be able to access user endpoints"
        
        # Admin should also be able to access user endpoint (this worked before)
        result = await user_endpoint_dependency(current_user=mock_users["admin"])
        assert result == mock_users["admin"], "Admin should be able to access user endpoints"
        
        # User should still be able to access user endpoint
        result = await user_endpoint_dependency(current_user=mock_users["user"])
        assert result == mock_users["user"], "User should be able to access user endpoints"

    @pytest.mark.asyncio
    async def test_hierarchical_access_works_for_all_combinations(self, mock_users):
        """
        Test that hierarchical access works correctly for all valid combinations.
        
        This validates the complete hierarchical role model.
        """
        # Test USER endpoint access
        user_endpoint = require_role(Role.USER)
        
        # All roles should be able to access user endpoints
        for role_name, user in mock_users.items():
            result = await user_endpoint(current_user=user)
            assert result == user, f"{role_name} should access user endpoints"
        
        # Test MODERATOR endpoint access  
        moderator_endpoint = require_role(Role.MODERATOR)
        
        # Only moderator and admin should access moderator endpoints
        result = await moderator_endpoint(current_user=mock_users["moderator"])
        assert result == mock_users["moderator"], "Moderator should access moderator endpoints"
        
        result = await moderator_endpoint(current_user=mock_users["admin"])
        assert result == mock_users["admin"], "Admin should access moderator endpoints"
        
        # User should be denied
        with pytest.raises(HTTPException) as exc:
            await moderator_endpoint(current_user=mock_users["user"])
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        
        # Test ADMIN endpoint access
        admin_endpoint = require_role(Role.ADMIN)
        
        # Only admin should access admin endpoints
        result = await admin_endpoint(current_user=mock_users["admin"])
        assert result == mock_users["admin"], "Admin should access admin endpoints"
        
        # User and moderator should be denied
        with pytest.raises(HTTPException) as exc:
            await admin_endpoint(current_user=mock_users["user"])
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        
        with pytest.raises(HTTPException) as exc:
            await admin_endpoint(current_user=mock_users["moderator"])
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_role_hierarchy_enforces_proper_levels(self, mock_users):
        """Test that the role hierarchy correctly enforces privilege levels."""
        # Verify role hierarchy order
        hierarchy = Role.get_hierarchy()
        assert hierarchy == [Role.USER, Role.MODERATOR, Role.ADMIN], "Role hierarchy should be in correct order"
        
        # Test can_access method directly
        assert Role.USER.can_access(Role.USER), "User should access user level"
        assert not Role.USER.can_access(Role.MODERATOR), "User should not access moderator level"
        assert not Role.USER.can_access(Role.ADMIN), "User should not access admin level"
        
        assert Role.MODERATOR.can_access(Role.USER), "Moderator should access user level"
        assert Role.MODERATOR.can_access(Role.MODERATOR), "Moderator should access moderator level"
        assert not Role.MODERATOR.can_access(Role.ADMIN), "Moderator should not access admin level"
        
        assert Role.ADMIN.can_access(Role.USER), "Admin should access user level"
        assert Role.ADMIN.can_access(Role.MODERATOR), "Admin should access moderator level"
        assert Role.ADMIN.can_access(Role.ADMIN), "Admin should access admin level"

    @pytest.mark.asyncio
    async def test_security_boundaries_maintained(self, mock_users):
        """Test that security boundaries are properly maintained."""
        # User trying to access moderator endpoint - should fail
        moderator_endpoint = require_role(Role.MODERATOR)
        with pytest.raises(HTTPException) as exc:
            await moderator_endpoint(current_user=mock_users["user"])
        
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Required role: moderator" in exc.value.detail
        assert "user role: user" in exc.value.detail
        
        # User trying to access admin endpoint - should fail
        admin_endpoint = require_role(Role.ADMIN)
        with pytest.raises(HTTPException) as exc:
            await admin_endpoint(current_user=mock_users["user"])
        
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Required role: admin" in exc.value.detail
        
        # Moderator trying to access admin endpoint - should fail
        with pytest.raises(HTTPException) as exc:
            await admin_endpoint(current_user=mock_users["moderator"])
        
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Required role: admin" in exc.value.detail
        assert "user role: moderator" in exc.value.detail

    def test_role_can_access_method_correctness(self):
        """Test that the Role.can_access() method works correctly for all combinations."""
        test_cases = [
            # (user_role, required_role, expected_result, description)
            (Role.USER, Role.USER, True, "User accessing user endpoint"),
            (Role.USER, Role.MODERATOR, False, "User accessing moderator endpoint"),
            (Role.USER, Role.ADMIN, False, "User accessing admin endpoint"),
            (Role.MODERATOR, Role.USER, True, "Moderator accessing user endpoint - KEY FIX"),
            (Role.MODERATOR, Role.MODERATOR, True, "Moderator accessing moderator endpoint"),
            (Role.MODERATOR, Role.ADMIN, False, "Moderator accessing admin endpoint"),
            (Role.ADMIN, Role.USER, True, "Admin accessing user endpoint"),
            (Role.ADMIN, Role.MODERATOR, True, "Admin accessing moderator endpoint"),
            (Role.ADMIN, Role.ADMIN, True, "Admin accessing admin endpoint"),
        ]
        
        for user_role, required_role, expected, description in test_cases:
            result = user_role.can_access(required_role)
            assert result == expected, f"Failed: {description} - expected {expected}, got {result}"

    @pytest.mark.asyncio
    async def test_original_issue_documented_behavior(self, mock_users):
        """
        Test the specific behavior mentioned in the original issue.
        
        Original issue: "Any route using require_role(Role.USER) will reject 
        moderators with a 403 despite them being more privileged"
        """
        # This is the exact scenario from the issue
        user_route_dependency = require_role(Role.USER)
        
        # Before fix: This would have raised HTTPException with 403
        # After fix: This should work without error
        moderator_user = mock_users["moderator"]
        
        # This should NOT raise an exception
        result = await user_route_dependency(current_user=moderator_user)
        assert result == moderator_user, "Moderator should be able to access Role.USER endpoints"
        
        # Verify that the response contains the moderator
        assert result.role == "moderator", "Returned user should be the moderator"
        assert result.username == "test_moderator", "Returned user should have correct username"

    @pytest.mark.asyncio 
    async def test_exact_role_functionality_still_works(self, mock_users):
        """Test that exact role matching functionality is still available when needed."""
        from services.orchestrator.roles import require_exact_role
        
        # Test exact role matching for moderator
        moderator_exact = require_exact_role(Role.MODERATOR)
        
        # Only moderator should pass
        result = await moderator_exact(current_user=mock_users["moderator"])
        assert result == mock_users["moderator"]
        
        # Admin should be denied for exact role matching
        with pytest.raises(HTTPException) as exc:
            await moderator_exact(current_user=mock_users["admin"])
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Required exact role: moderator" in exc.value.detail
        assert "user role: admin" in exc.value.detail


if __name__ == "__main__":
    pytest.main([__file__, "-v"])