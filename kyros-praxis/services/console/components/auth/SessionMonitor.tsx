'use client';

import { useSession } from 'next-auth/react';
import { useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';

interface SessionMonitorProps {
  children: React.ReactNode;
  refreshInterval?: number; // in minutes
  warningTime?: number; // in minutes before expiry
}

export default function SessionMonitor({ 
  children, 
  refreshInterval = 5, 
  warningTime = 2 
}: SessionMonitorProps) {
  const { data: session, status, update } = useSession();
  const router = useRouter();

  const refreshSession = useCallback(async () => {
    try {
      await update();
    } catch (error) {
      console.error('Failed to refresh session:', error);
      toast.error('Session refresh failed. Please log in again.');
      router.push('/auth');
    }
  }, [update, router]);

  const checkSessionExpiry = useCallback(() => {
    if (!session?.accessToken) return;

    try {
      const { jwtDecode } = require('jwt-decode');
      const decoded: any = jwtDecode(session.accessToken);
      const expiryTime = decoded.exp * 1000; // Convert to milliseconds
      const currentTime = Date.now();
      const timeUntilExpiry = expiryTime - currentTime;
      
      // Show warning if expiring soon
      if (timeUntilExpiry > 0 && timeUntilExpiry <= warningTime * 60 * 1000) {
        toast.warning('Your session will expire soon. Activity will refresh it automatically.', {
          duration: 5000,
          id: 'session-warning'
        });
      }
      
      // Auto-refresh if close to expiry
      if (timeUntilExpiry > 0 && timeUntilExpiry <= 60000) { // 1 minute
        refreshSession();
      }
    } catch (error) {
      console.error('Error checking session expiry:', error);
    }
  }, [session, warningTime, refreshSession]);

  // Set up session monitoring
  useEffect(() => {
    if (status !== 'authenticated') return;

    // Check immediately
    checkSessionExpiry();

    // Set up periodic checks
    const interval = setInterval(checkSessionExpiry, refreshInterval * 60 * 1000);
    
    return () => clearInterval(interval);
  }, [status, checkSessionExpiry, refreshInterval]);

  // Monitor user activity for auto-refresh
  useEffect(() => {
    if (status !== 'authenticated') return;

    let activityTimer: NodeJS.Timeout;

    const resetActivityTimer = () => {
      clearTimeout(activityTimer);
      activityTimer = setTimeout(() => {
        refreshSession();
      }, refreshInterval * 60 * 1000);
    };

    const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    
    activityEvents.forEach(event => {
      document.addEventListener(event, resetActivityTimer, true);
    });

    // Initial setup
    resetActivityTimer();

    return () => {
      clearTimeout(activityTimer);
      activityEvents.forEach(event => {
        document.removeEventListener(event, resetActivityTimer, true);
      });
    };
  }, [status, refreshSession, refreshInterval]);

  return <>{children}</>;
}