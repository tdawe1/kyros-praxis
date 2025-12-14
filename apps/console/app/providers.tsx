'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { ThemeProvider } from '@shared/ui/theme';

import { AuthProvider, useAuth } from './state/auth-context';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <AuthProvider>{children}</AuthProvider>
    </ThemeProvider>
  );
}

function AuthGate({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, setPendingRedirect } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const isAuthRoute = pathname?.startsWith('/login') || pathname?.startsWith('/signup');

  useEffect(() => {
    if (isLoading) {
      return;
    }
    if (!isAuthenticated && !isAuthRoute) {
      setPendingRedirect(pathname ?? '/landing');
      router.replace('/login');
    }
    if (isAuthenticated && isAuthRoute) {
      router.replace('/landing');
    }
  }, [isAuthenticated, isAuthRoute, router, isLoading, pathname, setPendingRedirect]);

  // While bootstrapping auth state, don't gate rendering
  if (isLoading) return null;

  // Allow unauthenticated users to access auth routes
  if (!isAuthenticated && isAuthRoute) return <>{children}</>;

  // Block protected routes when unauthenticated
  if (!isAuthenticated && !isAuthRoute) return null;

  // Prevent showing auth pages when already authenticated
  if (isAuthenticated && isAuthRoute) return null;

  return <>{children}</>;
}

export function ProtectedProviders({ children }: { children: React.ReactNode }) {
  return (
    <Providers>
      <AuthGate>{children}</AuthGate>
    </Providers>
  );
}
