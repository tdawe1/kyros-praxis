import { render, screen } from '@testing-library/react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import AuthGuard from '@/components/auth/AuthGuard';

// Mock NextAuth
jest.mock('next-auth/react', () => ({
  useSession: jest.fn()
}));

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn()
}));

const mockUseSession = useSession as jest.MockedFunction<typeof useSession>;
const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>;
const mockPush = jest.fn();

describe('AuthGuard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseRouter.mockReturnValue({
      push: mockPush,
      replace: jest.fn(),
      refresh: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      prefetch: jest.fn()
    } as any);
  });

  it('shows loading state while session is loading', () => {
    mockUseSession.mockReturnValue({
      data: null,
      status: 'loading'
    });

    render(
      <AuthGuard>
        <div>Protected Content</div>
      </AuthGuard>
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('shows protected content for authenticated users', () => {
    const mockSession = {
      user: {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        roles: ['user']
      },
      accessToken: 'mock-token'
    };

    mockUseSession.mockReturnValue({
      data: mockSession,
      status: 'authenticated'
    });

    render(
      <AuthGuard>
        <div>Protected Content</div>
      </AuthGuard>
    );

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('redirects unauthenticated users to login', () => {
    mockUseSession.mockReturnValue({
      data: null,
      status: 'unauthenticated'
    });

    render(
      <AuthGuard>
        <div>Protected Content</div>
      </AuthGuard>
    );

    expect(mockPush).toHaveBeenCalledWith('/auth');
  });

  it('shows access denied for users without required roles', () => {
    const mockSession = {
      user: {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        roles: ['user']
      },
      accessToken: 'mock-token'
    };

    mockUseSession.mockReturnValue({
      data: mockSession,
      status: 'authenticated'
    });

    render(
      <AuthGuard requiredRoles={['admin']}>
        <div>Admin Content</div>
      </AuthGuard>
    );

    expect(screen.getByText('Access Denied')).toBeInTheDocument();
    expect(screen.getByText('You don\'t have the required permissions to access this page.')).toBeInTheDocument();
  });

  it('shows content for users with required roles', () => {
    const mockSession = {
      user: {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        roles: ['admin', 'user']
      },
      accessToken: 'mock-token'
    };

    mockUseSession.mockReturnValue({
      data: mockSession,
      status: 'authenticated'
    });

    render(
      <AuthGuard requiredRoles={['admin']}>
        <div>Admin Content</div>
      </AuthGuard>
    );

    expect(screen.getByText('Admin Content')).toBeInTheDocument();
  });

  it('uses custom fallback component', () => {
    mockUseSession.mockReturnValue({
      data: null,
      status: 'loading'
    });

    render(
      <AuthGuard fallback={<div>Custom Loading</div>}>
        <div>Protected Content</div>
      </AuthGuard>
    );

    expect(screen.getByText('Custom Loading')).toBeInTheDocument();
  });
});