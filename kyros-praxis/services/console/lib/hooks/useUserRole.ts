/**
 * Custom hooks for role-based access control
 */

import { useSession } from 'next-auth/react';
import { UserRole, Permission, hasPermission, canAccessResource, getRolePermissions } from '../rbac';

/**
 * Hook to get the current user's role
 */
export function useUserRole(): {
  role: UserRole;
  isLoading: boolean;
  isAuthenticated: boolean;
} {
  const { data: session, status } = useSession();
  
  return {
    role: (session?.user as any)?.role || 'viewer',
    isLoading: status === 'loading',
    isAuthenticated: !!session,
  };
}

/**
 * Hook to check if current user has a specific permission
 */
export function useHasPermission(permission: Permission): boolean {
  const { role } = useUserRole();
  return hasPermission(role, permission);
}

/**
 * Hook to check if current user can access a resource
 */
export function useCanAccessResource(resource: string): boolean {
  const { role } = useUserRole();
  return canAccessResource(role, resource);
}

/**
 * Hook to get all permissions for the current user
 */
export function useUserPermissions(): Permission[] {
  const { role } = useUserRole();
  return getRolePermissions(role);
}

/**
 * Hook to check if current user has any of the specified roles
 */
export function useHasRole(allowedRoles: UserRole[]): boolean {
  const { role } = useUserRole();
  return allowedRoles.includes(role);
}