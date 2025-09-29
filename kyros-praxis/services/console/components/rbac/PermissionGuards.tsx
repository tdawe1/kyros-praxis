/**
 * RBAC Components for Permission-Based UI Rendering
 * 
 * These components provide role-based access control for UI elements,
 * allowing developers to conditionally render components based on user permissions.
 */

import { ReactNode } from 'react';
import { useSession } from 'next-auth/react';
import { UserRole, Permission, hasPermission, canAccessResource } from '../../lib/rbac';

interface PermissionGuardProps {
  children: ReactNode;
  permission: Permission;
  fallback?: ReactNode;
  userRole?: UserRole;
}

interface RoleGuardProps {
  children: ReactNode;
  allowedRoles: UserRole[];
  fallback?: ReactNode;
  userRole?: UserRole;
}

interface ResourceGuardProps {
  children: ReactNode;
  resource: string;
  fallback?: ReactNode;
  userRole?: UserRole;
}

/**
 * Component that renders children only if the user has the required permission
 */
export function PermissionGuard({ 
  children, 
  permission, 
  fallback = null, 
  userRole 
}: PermissionGuardProps) {
  const { data: session } = useSession();
  
  // Use provided userRole or get from session
  const currentRole = userRole || (session?.user as any)?.role || 'viewer';
  
  if (hasPermission(currentRole, permission)) {
    return <>{children}</>;
  }
  
  return <>{fallback}</>;
}

/**
 * Component that renders children only if the user has one of the allowed roles
 */
export function RoleGuard({ 
  children, 
  allowedRoles, 
  fallback = null, 
  userRole 
}: RoleGuardProps) {
  const { data: session } = useSession();
  
  // Use provided userRole or get from session
  const currentRole = userRole || (session?.user as any)?.role || 'viewer';
  
  if (allowedRoles.includes(currentRole)) {
    return <>{children}</>;
  }
  
  return <>{fallback}</>;
}

/**
 * Component that renders children only if the user can access the resource
 */
export function ResourceGuard({ 
  children, 
  resource, 
  fallback = null, 
  userRole 
}: ResourceGuardProps) {
  const { data: session } = useSession();
  
  // Use provided userRole or get from session
  const currentRole = userRole || (session?.user as any)?.role || 'viewer';
  
  if (canAccessResource(currentRole, resource)) {
    return <>{children}</>;
  }
  
  return <>{fallback}</>;
}

/**
 * Higher-order component that wraps a component with permission checking
 */
export function withPermission<T extends object>(
  Component: React.ComponentType<T>,
  permission: Permission,
  fallback?: ReactNode
) {
  return function PermissionWrappedComponent(props: T) {
    return (
      <PermissionGuard permission={permission} fallback={fallback}>
        <Component {...props} />
      </PermissionGuard>
    );
  };
}

/**
 * Higher-order component that wraps a component with role checking
 */
export function withRole<T extends object>(
  Component: React.ComponentType<T>,
  allowedRoles: UserRole[],
  fallback?: ReactNode
) {
  return function RoleWrappedComponent(props: T) {
    return (
      <RoleGuard allowedRoles={allowedRoles} fallback={fallback}>
        <Component {...props} />
      </RoleGuard>
    );
  };
}