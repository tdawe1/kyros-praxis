'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect, ReactNode } from 'react';

interface AuthGuardProps {
  children: ReactNode;
  requiredRoles?: string[];
  fallback?: ReactNode;
  redirectTo?: string;
}

export default function AuthGuard({ 
  children, 
  requiredRoles, 
  fallback = <div>Loading...</div>,
  redirectTo = '/auth'
}: AuthGuardProps) {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === 'loading') return; // Still loading

    if (!session) {
      router.push(redirectTo);
      return;
    }

    // Check role requirements
    if (requiredRoles && requiredRoles.length > 0) {
      const userRoles = (session.user as any)?.roles || [];
      const hasRequiredRole = requiredRoles.some(role => userRoles.includes(role));
      
      if (!hasRequiredRole) {
        router.push('/agents'); // Redirect to safe page
        return;
      }
    }
  }, [session, status, router, requiredRoles, redirectTo]);

  if (status === 'loading') {
    return <>{fallback}</>;
  }

  if (!session) {
    return <>{fallback}</>;
  }

  // Check role requirements
  if (requiredRoles && requiredRoles.length > 0) {
    const userRoles = (session.user as any)?.roles || [];
    const hasRequiredRole = requiredRoles.some(role => userRoles.includes(role));
    
    if (!hasRequiredRole) {
      return (
        <div className="p-4 text-center">
          <h2 className="text-xl font-semibold mb-2">Access Denied</h2>
          <p>You don&apos;t have the required permissions to access this page.</p>
        </div>
      );
    }
  }

  return <>{children}</>;
}