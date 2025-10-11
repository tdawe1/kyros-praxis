#!/usr/bin/env python3
"""
Final validation script to demonstrate that the role hierarchy issue is resolved.

This script creates a practical demonstration that the original issue:
"Denying elevated roles in role-based dependency" has been fixed.

It simulates the FastAPI dependency injection and validates that:
1. Moderators can access user endpoints (the main issue)
2. Admins can access user and moderator endpoints  
3. Security boundaries are maintained
4. The fix works in practice
"""

import sys
import os
import asyncio
from unittest.mock import Mock
from dataclasses import dataclass
from typing import Optional

# Add the services directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'orchestrator'))

try:
    from roles import Role, require_role, require_exact_role
    from fastapi import HTTPException, status
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the repository root.")
    sys.exit(1)


@dataclass
class MockUser:
    """Mock user for testing."""
    id: str
    username: str
    email: str
    role: str
    active: int = 1


class RoleHierarchyValidator:
    """Validator for role hierarchy functionality."""
    
    def __init__(self):
        self.test_users = {
            "user": MockUser("1", "testuser", "user@test.com", "user"),
            "moderator": MockUser("2", "testmoderator", "mod@test.com", "moderator"),
            "admin": MockUser("3", "testadmin", "admin@test.com", "admin")
        }
        self.results = []
    
    async def test_scenario(self, user_role: str, endpoint_role: Role, expected_success: bool, description: str):
        """Test a specific access scenario."""
        try:
            user = self.test_users[user_role]
            dependency = require_role(endpoint_role)
            
            # Call the dependency function
            result = await dependency(current_user=user)
            
            # If we get here, access was granted
            success = True
            error_msg = None
            
        except HTTPException as e:
            # Access was denied
            success = False
            error_msg = e.detail
        except Exception as e:
            # Unexpected error
            success = False
            error_msg = f"Unexpected error: {str(e)}"
        
        # Check if result matches expectation
        passed = success == expected_success
        status_icon = "✅" if passed else "❌"
        
        self.results.append({
            "description": description,
            "user_role": user_role,
            "endpoint_role": endpoint_role.value,
            "expected": expected_success,
            "actual": success,
            "passed": passed,
            "error": error_msg
        })
        
        print(f"{status_icon} {description}")
        if not passed:
            print(f"   Expected: {'ALLOW' if expected_success else 'DENY'}")
            print(f"   Actual:   {'ALLOW' if success else 'DENY'}")
            if error_msg:
                print(f"   Error:    {error_msg}")
        
        return passed
    
    async def test_exact_role_scenario(self, user_role: str, endpoint_role: Role, expected_success: bool, description: str):
        """Test exact role matching scenario."""
        try:
            user = self.test_users[user_role]
            dependency = require_exact_role(endpoint_role)
            
            result = await dependency(current_user=user)
            success = True
            error_msg = None
            
        except HTTPException as e:
            success = False
            error_msg = e.detail
        except Exception as e:
            success = False
            error_msg = f"Unexpected error: {str(e)}"
        
        passed = success == expected_success
        status_icon = "✅" if passed else "❌"
        
        print(f"{status_icon} {description} (exact role)")
        if not passed:
            print(f"   Expected: {'ALLOW' if expected_success else 'DENY'}")
            print(f"   Actual:   {'ALLOW' if success else 'DENY'}")
            if error_msg:
                print(f"   Error:    {error_msg}")
        
        return passed

    async def run_validation(self):
        """Run comprehensive validation of role hierarchy."""
        print("🔧 ROLE HIERARCHY VALIDATION")
        print("=" * 50)
        print("Testing the fix for: 'Denying elevated roles in role-based dependency'")
        print()
        
        # Critical scenarios that demonstrate the fix
        print("🎯 CRITICAL FIX SCENARIOS:")
        print("-" * 30)
        
        critical_tests = [
            ("moderator", Role.USER, True, "Moderator accessing USER endpoint (MAIN ISSUE)"),
            ("admin", Role.USER, True, "Admin accessing USER endpoint"),
            ("admin", Role.MODERATOR, True, "Admin accessing MODERATOR endpoint"),
        ]
        
        critical_passed = 0
        for user_role, endpoint_role, expected, description in critical_tests:
            if await self.test_scenario(user_role, endpoint_role, expected, description):
                critical_passed += 1
        
        print()
        print("🔒 SECURITY BOUNDARY VALIDATION:")
        print("-" * 35)
        
        security_tests = [
            ("user", Role.MODERATOR, False, "User accessing MODERATOR endpoint"),
            ("user", Role.ADMIN, False, "User accessing ADMIN endpoint"),
            ("moderator", Role.ADMIN, False, "Moderator accessing ADMIN endpoint"),
        ]
        
        security_passed = 0
        for user_role, endpoint_role, expected, description in security_tests:
            if await self.test_scenario(user_role, endpoint_role, expected, description):
                security_passed += 1
        
        print()
        print("✅ SAME-LEVEL ACCESS VALIDATION:")
        print("-" * 35)
        
        same_level_tests = [
            ("user", Role.USER, True, "User accessing USER endpoint"),
            ("moderator", Role.MODERATOR, True, "Moderator accessing MODERATOR endpoint"),
            ("admin", Role.ADMIN, True, "Admin accessing ADMIN endpoint"),
        ]
        
        same_level_passed = 0
        for user_role, endpoint_role, expected, description in same_level_tests:
            if await self.test_scenario(user_role, endpoint_role, expected, description):
                same_level_passed += 1
        
        print()
        print("🎯 EXACT ROLE MATCHING:")
        print("-" * 25)
        
        exact_passed = 0
        exact_tests = [
            ("moderator", Role.MODERATOR, True, "Moderator accessing moderator-exact endpoint"),
            ("admin", Role.MODERATOR, False, "Admin accessing moderator-exact endpoint"),
            ("user", Role.MODERATOR, False, "User accessing moderator-exact endpoint"),
        ]
        
        for user_role, endpoint_role, expected, description in exact_tests:
            if await self.test_exact_role_scenario(user_role, endpoint_role, expected, description):
                exact_passed += 1
        
        # Summary
        total_critical = len(critical_tests)
        total_security = len(security_tests)
        total_same_level = len(same_level_tests)
        total_exact = len(exact_tests)
        
        print()
        print("=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)
        print(f"Critical fix scenarios:   {critical_passed}/{total_critical} ✅")
        print(f"Security boundaries:      {security_passed}/{total_security} ✅")
        print(f"Same-level access:        {same_level_passed}/{total_same_level} ✅")
        print(f"Exact role matching:      {exact_passed}/{total_exact} ✅")
        print()
        
        all_passed = (
            critical_passed == total_critical and
            security_passed == total_security and
            same_level_passed == total_same_level and
            exact_passed == total_exact
        )
        
        if all_passed:
            print("🎉 VALIDATION RESULT: ✅ ALL TESTS PASSED!")
            print("✅ The original issue has been RESOLVED")
            print("✅ Role hierarchy is working correctly")
            print("✅ Security boundaries are maintained")
            print("✅ System is ready for production")
        else:
            print("❌ VALIDATION RESULT: Some tests failed")
            print("❌ The role hierarchy needs additional work")
        
        print()
        return all_passed
    
    def show_implementation_summary(self):
        """Show summary of the implementation."""
        print("📋 IMPLEMENTATION SUMMARY")
        print("=" * 30)
        print("The role hierarchy system works as follows:")
        print()
        print("1. Role Hierarchy (lowest to highest privilege):")
        hierarchy = Role.get_hierarchy()
        for i, role in enumerate(hierarchy):
            print(f"   {i}. {role.value.upper()}")
        print()
        print("2. Access Rules:")
        print("   • Higher roles can access lower role endpoints")
        print("   • Same role level has access")
        print("   • Lower roles cannot access higher endpoints")
        print()
        print("3. Implementation:")
        print("   • Role.can_access(required_role) checks hierarchy")
        print("   • require_role() uses hierarchical access control")
        print("   • require_exact_role() for role-specific functionality")
        print()
        print("4. Usage Examples:")
        print("   @router.get('/user-content')")
        print("   async def get_content(user = Depends(require_role(Role.USER))):")
        print("       # Accessible by user, moderator, admin")
        print("       return {'content': 'data'}")
        print()


async def main():
    """Run the complete validation."""
    validator = RoleHierarchyValidator()
    
    # Run validation
    success = await validator.run_validation()
    
    # Show implementation details
    validator.show_implementation_summary()
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error running validation: {e}")
        sys.exit(1)