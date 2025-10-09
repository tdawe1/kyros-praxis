#!/usr/bin/env python3
"""
Demonstration script for hierarchical role-based access control fix.

This script demonstrates how the new role hierarchy system resolves the
original issue where elevated roles (moderator, admin) were denied access
to endpoints requiring lower roles (user).

ORIGINAL ISSUE:
- require_role(Role.USER) would deny moderators and admins
- Higher privilege roles couldn't access lower privilege endpoints
- This broke the expected role model hierarchy

SOLUTION:
- Implemented Role enum with can_access() method 
- Added require_role() dependency with hierarchical logic
- Higher roles can now access endpoints requiring lower roles
- Maintains security by preventing lower roles from accessing higher endpoints
"""

import sys
import os

# Add the services directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'orchestrator'))

from enum import Enum
from typing import List

class Role(Enum):
    """
    User role enumeration with hierarchical ordering.
    
    Roles are ordered from lowest to highest privilege level.
    Higher privilege roles can access endpoints that require lower privilege roles.
    """
    USER = "user"
    MODERATOR = "moderator" 
    ADMIN = "admin"
    
    @classmethod
    def get_hierarchy(cls) -> List["Role"]:
        """Get role hierarchy from lowest to highest privilege."""
        return [cls.USER, cls.MODERATOR, cls.ADMIN]
    
    def can_access(self, required_role: "Role") -> bool:
        """
        Check if this role can access an endpoint requiring the specified role.
        
        Higher privilege roles can access endpoints that require lower privilege roles.
        """
        hierarchy = self.get_hierarchy()
        current_level = hierarchy.index(self)
        required_level = hierarchy.index(required_role)
        
        # Higher or equal privilege level can access
        return current_level >= required_level


def simulate_old_behavior(user_role: Role, required_role: Role) -> bool:
    """Simulate the old behavior where only exact role matches were allowed."""
    return user_role == required_role or user_role == Role.ADMIN  # Admin special case


def demonstrate_fix():
    """Demonstrate the role hierarchy fix."""
    print("🔧 ROLE-BASED ACCESS CONTROL FIX DEMONSTRATION")
    print("=" * 60)
    print()
    
    # Show role hierarchy
    print("📊 ROLE HIERARCHY (lowest to highest privilege):")
    hierarchy = Role.get_hierarchy()
    for i, role in enumerate(hierarchy):
        print(f"  {i + 1}. {role.value.upper()}")
    print()
    
    # Test scenarios
    scenarios = [
        (Role.USER, Role.USER, "User accessing user content"),
        (Role.MODERATOR, Role.USER, "Moderator accessing user content"),
        (Role.ADMIN, Role.USER, "Admin accessing user content"),
        (Role.USER, Role.MODERATOR, "User accessing moderator content"),
        (Role.MODERATOR, Role.MODERATOR, "Moderator accessing moderator content"), 
        (Role.ADMIN, Role.MODERATOR, "Admin accessing moderator content"),
        (Role.USER, Role.ADMIN, "User accessing admin content"),
        (Role.MODERATOR, Role.ADMIN, "Moderator accessing admin content"),
        (Role.ADMIN, Role.ADMIN, "Admin accessing admin content"),
    ]
    
    print("🔍 ACCESS CONTROL COMPARISON:")
    print("-" * 60)
    print(f"{'SCENARIO':<35} {'OLD':<8} {'NEW':<8} {'STATUS'}")
    print("-" * 60)
    
    for user_role, required_role, description in scenarios:
        old_result = simulate_old_behavior(user_role, required_role)
        new_result = user_role.can_access(required_role)
        
        # Determine status
        if old_result == new_result:
            status = "✓ Same"
        elif not old_result and new_result:
            status = "🔧 FIXED"
        else:
            status = "❌ Broken"
        
        old_str = "ALLOW" if old_result else "DENY"
        new_str = "ALLOW" if new_result else "DENY"
        
        print(f"{description:<35} {old_str:<8} {new_str:<8} {status}")
    
    print()
    print("🎯 KEY FIXES:")
    print("  • Moderators can now access user endpoints")
    print("  • Admins can now access user and moderator endpoints")
    print("  • Security is maintained - lower roles cannot access higher endpoints")
    print("  • Role hierarchy is properly implemented")
    print()
    
    # Show specific issue resolution
    print("🐛 ORIGINAL ISSUE RESOLUTION:")
    print("-" * 40)
    print("Issue: 'require_role(Role.USER) will reject moderators with a 403'")
    print()
    print("Before fix:")
    print(f"  • Moderator accessing USER endpoint: {'DENIED (403)' if not simulate_old_behavior(Role.MODERATOR, Role.USER) else 'ALLOWED'}")
    print(f"  • Admin accessing USER endpoint: {'DENIED (403)' if not simulate_old_behavior(Role.ADMIN, Role.USER) else 'ALLOWED'}")
    print()
    print("After fix:")
    print(f"  • Moderator accessing USER endpoint: {'ALLOWED ✓' if Role.MODERATOR.can_access(Role.USER) else 'DENIED'}")
    print(f"  • Admin accessing USER endpoint: {'ALLOWED ✓' if Role.ADMIN.can_access(Role.USER) else 'DENIED'}")
    print()
    print("✅ Issue resolved! Higher roles can now access lower role endpoints.")


def show_implementation_details():
    """Show implementation details of the fix."""
    print()
    print("🔧 IMPLEMENTATION DETAILS:")
    print("-" * 40)
    print()
    print("1. Role Enum with Hierarchy:")
    print("   - USER (level 0)")
    print("   - MODERATOR (level 1)") 
    print("   - ADMIN (level 2)")
    print()
    print("2. Access Logic:")
    print("   - current_level >= required_level allows access")
    print("   - Higher privilege roles inherit lower role permissions")
    print()
    print("3. FastAPI Dependencies:")
    print("   - require_role(Role.USER) allows user, moderator, admin")
    print("   - require_role(Role.MODERATOR) allows moderator, admin")
    print("   - require_role(Role.ADMIN) allows admin only")
    print()
    print("4. Example Usage:")
    print("   @app.get('/user-content')")
    print("   async def get_content(user: User = Depends(require_role(Role.USER))):")
    print("       # Accessible by all authenticated users")
    print("       return {'content': 'user data'}")
    print()


if __name__ == "__main__":
    demonstrate_fix()
    show_implementation_details()