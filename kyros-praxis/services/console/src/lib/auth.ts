"use client";
import { jwtDecode } from "jwt-decode";
import * as React from "react";

// Define the user type
interface User {
  id: string;
  email: string;
  name: string;
  // Add other fields as per your user model
}

// Define the auth context type
interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = React.createContext<AuthContextType | null>(null);

// Custom hook for JWT auth
export const useAuth = () => {
  const [user, setUser] = React.useState<User | null>(null);
  const [token, setToken] = React.useState<string | null>(null);

  React.useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      try {
        const decoded: any = jwtDecode(token);
        setUser({
          id: decoded.sub || decoded.id,
          email: decoded.email,
          name: decoded.name,
        });
        setToken(token);
      } catch (error) {
        console.error("Invalid token", error);
        localStorage.removeItem("token");
        setUser(null);
        setToken(null);
      }
    }
  }, []);

  const login = (newToken: string) => {
    localStorage.setItem("token", newToken);
    try {
      const decoded: any = jwtDecode(newToken);
      setUser({
        id: decoded.sub || decoded.id,
        email: decoded.email,
        name: decoded.name,
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

  return {
    user,
    token,
    login,
    logout,
  };
};

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const auth = useAuth();

  return React.createElement(
    AuthContext.Provider,
    {
      value: auth,
    },
    children
  );
};
