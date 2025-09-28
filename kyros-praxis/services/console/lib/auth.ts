import { jwtDecode } from "jwt-decode";
import React, { useState, useEffect, createContext, createElement, useContext, ReactNode } from "react";

// Define the user type
interface User {
  id: string;
  email: string;
  name: string;
  roles?: string[];
  // Add other fields as per your user model
}

// Define the auth context type
interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string) => void;
  logout: () => void;
  isLoading: boolean;
  isTokenExpired: () => boolean;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

// Token validation utility
const isTokenExpired = (token: string): boolean => {
  try {
    const decoded: any = jwtDecode(token);
    const currentTime = Date.now() / 1000;
    return decoded.exp < currentTime;
  } catch {
    return true;
  }
};

// Custom hook for JWT auth
export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      setIsLoading(true);
      const token = localStorage.getItem("token");
      if (token && !isTokenExpired(token)) {
        try {
          const decoded: any = jwtDecode(token);
          setUser({
            id: decoded.sub || decoded.id,
            email: decoded.email,
            name: decoded.name,
            roles: decoded.roles || [],
          });
          setToken(token);
        } catch (error) {
          console.error("Invalid token", error);
          localStorage.removeItem("token");
          setUser(null);
          setToken(null);
        }
      } else if (token) {
        // Token expired, try to refresh
        try {
          await refreshTokenInternal();
        } catch {
          localStorage.removeItem("token");
          setUser(null);
          setToken(null);
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const refreshTokenInternal = async (): Promise<void> => {
    try {
      // Try to get fresh token from NextAuth session
      const { getSession } = await import('next-auth/react');
      const session: any = await getSession();
      
      if (session?.accessToken) {
        const decoded: any = jwtDecode(session.accessToken);
        setUser({
          id: decoded.sub || decoded.id,
          email: decoded.email,
          name: decoded.name,
          roles: decoded.roles || [],
        });
        setToken(session.accessToken);
        localStorage.setItem("token", session.accessToken);
      } else {
        throw new Error('No valid session');
      }
    } catch (error) {
      console.error("Token refresh failed", error);
      throw error;
    }
  };

  const login = (newToken: string) => {
    localStorage.setItem("token", newToken);
    try {
      const decoded: any = jwtDecode(newToken);
      setUser({
        id: decoded.sub || decoded.id,
        email: decoded.email,
        name: decoded.name,
        roles: decoded.roles || [],
      });
      setToken(newToken);
    } catch (error) {
      console.error("Invalid token", error);
      localStorage.removeItem("token");
      setUser(null);
      setToken(null);
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
    setToken(null);
  };

  const checkTokenExpired = (): boolean => {
    if (!token) return true;
    return isTokenExpired(token);
  };

  const refreshToken = async (): Promise<void> => {
    await refreshTokenInternal();
  };

  return {
    user,
    token,
    login,
    logout,
    isLoading,
    isTokenExpired: checkTokenExpired,
    refreshToken,
  };
};

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const auth = useAuth();

  return createElement(
    AuthContext.Provider,
    {
      value: auth,
    },
    children
  );
};

// Hook to use auth context
export const useAuthContext = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
};

// Higher-order component for protected routes
export function withAuth<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  requiredRoles?: string[]
) {
  return function AuthenticatedComponent(props: P): ReactNode {
    const { user, isLoading } = useAuthContext();

    if (isLoading) {
      return React.createElement('div', null, 'Loading...');
    }

    if (!user) {
      // Redirect to login will be handled by middleware
      return null;
    }

    if (requiredRoles && !requiredRoles.some(role => user.roles?.includes(role))) {
      return React.createElement('div', null, 'Access denied. Insufficient permissions.');
    }

    return React.createElement(WrappedComponent, props);
  };
}
