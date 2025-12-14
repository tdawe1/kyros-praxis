'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import type { ReactNode } from 'react';

import { ACCESS_TOKEN_STORAGE_KEY, API_BASE } from '../lib/api';
import { api, apiClient } from '../lib/api-client';

type User = {
  id: string;
  username: string;
  email: string;
  role: string;
  active: boolean;
  created_at: string;
};

type AuthContextValue = {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
  isTokenValid: () => boolean;
  setPendingRedirect: (path: string | null) => void;
  pendingRedirect: string | null;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// NOTE: Token management moved to httpOnly cookies
// Tokens are now automatically handled by the browser
// No need for localStorage (better security - XSS protection)

const safeReadToken = () => {
  // Deprecated: Tokens now in httpOnly cookies
  // Kept for backward compatibility during migration
  return null;
};

const safeStoreToken = (token: string | null) => {
  // Deprecated: Tokens now in httpOnly cookies  
  // Kept for backward compatibility during migration
};

const jsonHeaders = {
  'Content-Type': 'application/json',
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const bootstrapped = useRef(false);
  const [pendingRedirect, setPendingRedirect] = useState<string | null>(null);

  const fetchCurrentUser = useCallback(async () => {
    try {
      setIsLoading(true);
      // Avoid auto-refresh redirect loops on public pages
      const data = await apiClient<User>('/auth/me', { method: 'GET', skipRefresh: true });
      setUser(data);
      setToken('cookie-auth');
    } catch (error: any) {
      if (error?.status === 401) {
        setUser(null);
        setToken(null);
        return;
      }
      console.error('Failed to fetch current user', error);
      setUser(null);
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refresh = useCallback(async () => {
    // Use apiClient with skipRefresh to avoid recursive refresh
    try {
      setIsLoading(true);
      await apiClient('/auth/refresh', { method: 'POST', skipRefresh: true });
      await fetchCurrentUser();
    } catch (error) {
      console.error('Failed to refresh token', error);
      setUser(null);
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  }, [fetchCurrentUser]);

  useEffect(() => {
    if (bootstrapped.current) {
      return;
    }
    bootstrapped.current = true;
    
    // Try to fetch current user (cookie-based auth)
    // If cookies exist, this will succeed
    fetchCurrentUser().catch(() => {
      // No valid cookies, user needs to login
    });
  }, [fetchCurrentUser]);

  // Removed: Token state management now handled by cookies

  const login = useCallback(async (email: string, password: string) => {
    try {
      setIsLoading(true);
      await api.post('/auth/login', { email, password });
    } catch (error: any) {
      const message = error?.response?.detail ?? 'Invalid email or password.';
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
    setToken('cookie-auth');
    await fetchCurrentUser();
    if (typeof window !== 'undefined') {
      window.location.replace(pendingRedirect ?? '/landing');
      setPendingRedirect(null);
    }
  }, [fetchCurrentUser, pendingRedirect]);

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Logout request failed', error);
    }
    setToken(null);
    setUser(null);
    setIsLoading(false);
  }, []);

  const register = useCallback(async (username: string, email: string, password: string) => {
    try {
      await api.post('/auth/register', { username, email, password });
    } catch (error: any) {
      const message = error?.response?.detail ?? 'Registration failed. Try a different email or username.';
      throw new Error(message);
    }
    await login(email, password);
  }, [login]);

  const isTokenValid = useCallback(() => {
    // With httpOnly cookies, we can't check token validity client-side
    // Token is secure in cookie, inaccessible to JavaScript
    // Return true if user is loaded (indicates valid session)
    return Boolean(user);
  }, [user]);

  // Auto-refresh token before expiry
  useEffect(() => {
    if (!user) {
      return;
    }

    // Refresh token every 10 minutes (access token expires in 15)
    const refreshInterval = setInterval(() => {
      refresh().catch(() => {
        // Refresh failed, logout
        logout();
      });
    }, 10 * 60 * 1000); // 10 minutes

    return () => clearInterval(refreshInterval);
  }, [user, refresh, logout]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(user && token),
      isLoading,
      login,
      register,
      logout,
      refresh,
      isTokenValid,
      setPendingRedirect,
      pendingRedirect,
    }),
    [
      user,
      token,
      isLoading,
      login,
      register,
      logout,
      refresh,
      isTokenValid,
      setPendingRedirect,
      pendingRedirect,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
 const context = useContext(AuthContext);
 if (!context) {
   throw new Error('useAuth must be used within an AuthProvider');
 }
 return context;
}
