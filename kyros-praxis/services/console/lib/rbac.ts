/**
 * Role-Based Access Control (RBAC) Types and Constants
 * 
 * This file defines the permission system used throughout the console application.
 * It includes role definitions, permission mappings, and utility types for access control.
 */

export type UserRole = 'viewer' | 'editor' | 'admin' | 'integrator';

export interface Permission {
  resource: string;
  action: 'read' | 'write' | 'delete' | 'admin';
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  active: boolean;
  created_at: string;
}

// Define permissions for each resource
export const PERMISSIONS = {
  AGENTS: {
    READ: { resource: 'agents', action: 'read' as const },
    WRITE: { resource: 'agents', action: 'write' as const },
    DELETE: { resource: 'agents', action: 'delete' as const },
    ADMIN: { resource: 'agents', action: 'admin' as const },
  },
  JOBS: {
    READ: { resource: 'jobs', action: 'read' as const },
    WRITE: { resource: 'jobs', action: 'write' as const },
    DELETE: { resource: 'jobs', action: 'delete' as const },
    ADMIN: { resource: 'jobs', action: 'admin' as const },
  },
  TASKS: {
    READ: { resource: 'tasks', action: 'read' as const },
    WRITE: { resource: 'tasks', action: 'write' as const },
    DELETE: { resource: 'tasks', action: 'delete' as const },
    ADMIN: { resource: 'tasks', action: 'admin' as const },
  },
  EVENTS: {
    READ: { resource: 'events', action: 'read' as const },
    WRITE: { resource: 'events', action: 'write' as const },
    DELETE: { resource: 'events', action: 'delete' as const },
    ADMIN: { resource: 'events', action: 'admin' as const },
  },
  SYSTEM: {
    READ: { resource: 'system', action: 'read' as const },
    WRITE: { resource: 'system', action: 'write' as const },
    DELETE: { resource: 'system', action: 'delete' as const },
    ADMIN: { resource: 'system', action: 'admin' as const },
  },
  USERS: {
    READ: { resource: 'users', action: 'read' as const },
    WRITE: { resource: 'users', action: 'write' as const },
    DELETE: { resource: 'users', action: 'delete' as const },
    ADMIN: { resource: 'users', action: 'admin' as const },
  },
} as const;

// Define base permissions first to avoid circular reference
const viewerPermissions: Permission[] = [
  PERMISSIONS.AGENTS.READ,
  PERMISSIONS.JOBS.READ,
  PERMISSIONS.TASKS.READ,
  PERMISSIONS.EVENTS.READ,
  PERMISSIONS.SYSTEM.READ,
];

const editorPermissions: Permission[] = [
  ...viewerPermissions,
  PERMISSIONS.AGENTS.WRITE,
  PERMISSIONS.JOBS.WRITE,
  PERMISSIONS.TASKS.WRITE,
  PERMISSIONS.EVENTS.WRITE,
];

const integratorPermissions: Permission[] = [
  PERMISSIONS.AGENTS.READ,
  PERMISSIONS.AGENTS.WRITE,
  PERMISSIONS.JOBS.READ,
  PERMISSIONS.JOBS.WRITE,
  PERMISSIONS.TASKS.READ,
  PERMISSIONS.TASKS.WRITE,
  PERMISSIONS.EVENTS.READ,
  PERMISSIONS.SYSTEM.READ,
];

const adminPermissions: Permission[] = [
  // Full access to everything
  ...Object.values(PERMISSIONS).flatMap(resource => Object.values(resource)),
];

// Role-based permission mappings
export const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  viewer: viewerPermissions,
  editor: editorPermissions,
  integrator: integratorPermissions,
  admin: adminPermissions,
};

// Permission inheritance hierarchy
export const ROLE_HIERARCHY: Record<UserRole, UserRole[]> = {
  viewer: [],
  editor: ['viewer'],
  integrator: ['viewer'],
  admin: ['viewer', 'editor', 'integrator'],
};

/**
 * Check if a user role has a specific permission
 */
export function hasPermission(userRole: UserRole, permission: Permission): boolean {
  const rolePermissions = ROLE_PERMISSIONS[userRole] || [];
  
  // Check direct permissions
  const hasDirectPermission = rolePermissions.some(
    p => p.resource === permission.resource && p.action === permission.action
  );
  
  if (hasDirectPermission) return true;
  
  // Check inherited permissions from role hierarchy
  const inheritedRoles = ROLE_HIERARCHY[userRole] || [];
  return inheritedRoles.some(inheritedRole => 
    hasPermission(inheritedRole, permission)
  );
}

/**
 * Check if a user role can access a specific resource with any action
 */
export function canAccessResource(userRole: UserRole, resource: string): boolean {
  const rolePermissions = ROLE_PERMISSIONS[userRole] || [];
  
  // Check direct permissions
  const hasDirectAccess = rolePermissions.some(p => p.resource === resource);
  if (hasDirectAccess) return true;
  
  // Check inherited permissions
  const inheritedRoles = ROLE_HIERARCHY[userRole] || [];
  return inheritedRoles.some(inheritedRole => 
    canAccessResource(inheritedRole, resource)
  );
}

/**
 * Get all permissions for a user role (including inherited)
 */
export function getRolePermissions(userRole: UserRole): Permission[] {
  const directPermissions = ROLE_PERMISSIONS[userRole] || [];
  const inheritedRoles = ROLE_HIERARCHY[userRole] || [];
  
  const inheritedPermissions = inheritedRoles.flatMap(role => 
    ROLE_PERMISSIONS[role] || []
  );
  
  // Remove duplicates
  const allPermissions = [...directPermissions, ...inheritedPermissions];
  return allPermissions.filter((permission, index, array) => 
    array.findIndex(p => 
      p.resource === permission.resource && p.action === permission.action
    ) === index
  );
}