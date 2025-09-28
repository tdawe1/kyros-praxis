/**
 * @jest-environment jsdom
 */

import { render, screen } from '@testing-library/react';
import { PermissionGuard, RoleGuard, ResourceGuard } from '../components/rbac/PermissionGuards';
import { PERMISSIONS } from '../lib/rbac';

// Mock next-auth/react
jest.mock('next-auth/react', () => ({
  useSession: jest.fn(),
  SessionProvider: ({ children }: { children: React.ReactNode }) => children,
}));

import { useSession } from 'next-auth/react';
const mockUseSession = useSession as jest.MockedFunction<typeof useSession>;

describe('RBAC Components', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('PermissionGuard', () => {
    it('should render children for admin users', () => {
      mockUseSession.mockReturnValue({
        data: {
          user: { role: 'admin' },
          expires: '',
        },
        status: 'authenticated',
      });

      render(
        <PermissionGuard permission={PERMISSIONS.AGENTS.WRITE}>
          <div>Admin Content</div>
        </PermissionGuard>
      );
      
      expect(screen.getByText('Admin Content')).toBeInTheDocument();
    });

    it('should render children for editor users with write permission', () => {
      mockUseSession.mockReturnValue({
        data: {
          user: { role: 'editor' },
          expires: '',
        },
        status: 'authenticated',
      });

      render(
        <PermissionGuard permission={PERMISSIONS.AGENTS.WRITE}>
          <div>Editor Content</div>
        </PermissionGuard>
      );
      
      expect(screen.getByText('Editor Content')).toBeInTheDocument();
    });

    it('should not render children for viewer users without write permission', () => {
      mockUseSession.mockReturnValue({
        data: {
          user: { role: 'viewer' },
          expires: '',
        },
        status: 'authenticated',
      });

      render(
        <PermissionGuard permission={PERMISSIONS.AGENTS.WRITE}>
          <div>Restricted Content</div>
        </PermissionGuard>
      );
      
      expect(screen.queryByText('Restricted Content')).not.toBeInTheDocument();
    });

    it('should render fallback for unauthorized users', () => {
      mockUseSession.mockReturnValue({
        data: {
          user: { role: 'viewer' },
          expires: '',
        },
        status: 'authenticated',
      });

      render(
        <PermissionGuard 
          permission={PERMISSIONS.AGENTS.WRITE}
          fallback={<div>Access Denied</div>}
        >
          <div>Restricted Content</div>
        </PermissionGuard>
      );
      
      expect(screen.getByText('Access Denied')).toBeInTheDocument();
      expect(screen.queryByText('Restricted Content')).not.toBeInTheDocument();
    });
  });

  describe('RoleGuard', () => {
    it('should render children for allowed roles', () => {
      mockUseSession.mockReturnValue({
        data: {
          user: { role: 'editor' },
          expires: '',
        },
        status: 'authenticated',
      });

      render(
        <RoleGuard allowedRoles={['editor', 'admin']}>
          <div>Editor/Admin Content</div>
        </RoleGuard>
      );
      
      expect(screen.getByText('Editor/Admin Content')).toBeInTheDocument();
    });

    it('should not render children for disallowed roles', () => {
      mockUseSession.mockReturnValue({
        data: {
          user: { role: 'viewer' },
          expires: '',
        },
        status: 'authenticated',
      });

      render(
        <RoleGuard allowedRoles={['editor', 'admin']}>
          <div>Restricted Content</div>
        </RoleGuard>
      );
      
      expect(screen.queryByText('Restricted Content')).not.toBeInTheDocument();
    });
  });

  describe('ResourceGuard', () => {
    it('should render children for users with resource access', () => {
      mockUseSession.mockReturnValue({
        data: {
          user: { role: 'editor' },
          expires: '',
        },
        status: 'authenticated',
      });

      render(
        <ResourceGuard resource="agents">
          <div>Agents Content</div>
        </ResourceGuard>
      );
      
      expect(screen.getByText('Agents Content')).toBeInTheDocument();
    });

    it('should render children for viewers with read-only resource access', () => {
      mockUseSession.mockReturnValue({
        data: {
          user: { role: 'viewer' },
          expires: '',
        },
        status: 'authenticated',
      });

      render(
        <ResourceGuard resource="agents">
          <div>Agents View Content</div>
        </ResourceGuard>
      );
      
      expect(screen.getByText('Agents View Content')).toBeInTheDocument();
    });

    it('should not render children for users without resource access', () => {
      mockUseSession.mockReturnValue({
        data: {
          user: { role: 'viewer' },
          expires: '',
        },
        status: 'authenticated',
      });

      render(
        <ResourceGuard resource="users">
          <div>Users Management</div>
        </ResourceGuard>
      );
      
      expect(screen.queryByText('Users Management')).not.toBeInTheDocument();
    });
  });
});