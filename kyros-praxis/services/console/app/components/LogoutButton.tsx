"use client";

import { signOut, useSession } from "next-auth/react";
import { useState } from "react";

interface LogoutButtonProps {
  className?: string;
  children?: React.ReactNode;
}

export default function LogoutButton({ className = "", children }: LogoutButtonProps) {
  const { data: session } = useSession();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      // Clear localStorage token for API fallback
      localStorage.removeItem('token');
      
      // Sign out using NextAuth
      await signOut({
        callbackUrl: '/auth',
        redirect: true,
      });
    } catch (error) {
      console.error('Logout failed:', error);
      setIsLoggingOut(false);
    }
  };

  if (!session) {
    return null;
  }

  return (
    <button
      onClick={handleLogout}
      disabled={isLoggingOut}
      className={`${className} disabled:opacity-60 disabled:cursor-not-allowed`}
    >
      {children || (isLoggingOut ? 'Signing out...' : 'Sign out')}
    </button>
  );
}