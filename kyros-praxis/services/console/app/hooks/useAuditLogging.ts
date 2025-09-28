/**
 * React hook for audit logging in components
 * 
 * Provides convenient methods for logging user interactions and component events
 */

import { useCallback, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { usePathname } from 'next/navigation';
import {
  auditLogger,
  AuditEventType,
  AuditSeverity,
  auditUserAction,
  auditDataAccess,
  auditSecurityIncident,
} from '../lib/audit';

export interface UseAuditLoggingOptions {
  trackPageViews?: boolean;
  trackFormSubmissions?: boolean;
  trackButtonClicks?: boolean;
  component?: string;
}

export function useAuditLogging(options: UseAuditLoggingOptions = {}) {
  const { data: session } = useSession();
  const pathname = usePathname();
  
  const {
    trackPageViews = true,
    trackFormSubmissions = true,
    trackButtonClicks = true,
    component = 'unknown',
  } = options;

  const userId = session?.user?.id || session?.user?.email || undefined;
  const userEmail = session?.user?.email || undefined;

  // Track page views automatically
  useEffect(() => {
    if (trackPageViews && pathname) {
      auditLogger.log(AuditEventType.PAGE_VIEW, {
        userId,
        userEmail,
        resource: pathname,
        action: 'view',
        details: {
          component,
          timestamp: new Date().toISOString(),
        },
      });
    }
  }, [pathname, trackPageViews, userId, userEmail, component]);

  // Log user action with context
  const logAction = useCallback(
    async (
      action: string,
      details?: Record<string, any>,
      resource?: string
    ) => {
      await auditUserAction(
        action,
        resource || pathname || component,
        userId,
        {
          component,
          userEmail,
          ...details,
        }
      );
    },
    [userId, userEmail, pathname, component]
  );

  // Log form submission
  const logFormSubmit = useCallback(
    async (formName: string, formData?: Record<string, any>) => {
      if (!trackFormSubmissions) return;

      await auditLogger.log(AuditEventType.FORM_SUBMIT, {
        userId,
        userEmail,
        resource: pathname,
        action: 'form_submit',
        details: {
          component,
          formName,
          formData: formData ? Object.keys(formData) : undefined, // Don't log sensitive data
          timestamp: new Date().toISOString(),
        },
      });
    },
    [trackFormSubmissions, userId, userEmail, pathname, component]
  );

  // Log button click
  const logButtonClick = useCallback(
    async (buttonId: string, buttonText?: string, additionalDetails?: Record<string, any>) => {
      if (!trackButtonClicks) return;

      await auditLogger.log(AuditEventType.BUTTON_CLICK, {
        userId,
        userEmail,
        resource: pathname,
        action: 'button_click',
        details: {
          component,
          buttonId,
          buttonText,
          timestamp: new Date().toISOString(),
          ...additionalDetails,
        },
      });
    },
    [trackButtonClicks, userId, userEmail, pathname, component]
  );

  // Log data access operations
  const logDataOperation = useCallback(
    async (
      operation: 'read' | 'create' | 'update' | 'delete' | 'export',
      resourceName: string,
      resourceId?: string,
      additionalDetails?: Record<string, any>
    ) => {
      await auditDataAccess(
        operation,
        resourceName,
        userId,
        {
          component,
          userEmail,
          resourceId,
          timestamp: new Date().toISOString(),
          ...additionalDetails,
        }
      );
    },
    [userId, userEmail, component]
  );

  // Log security incident
  const logSecurityIncident = useCallback(
    async (
      type: AuditEventType,
      severity: AuditSeverity,
      message: string,
      additionalDetails?: Record<string, any>
    ) => {
      await auditSecurityIncident(
        type,
        severity,
        userId,
        {
          component,
          userEmail,
          message,
          timestamp: new Date().toISOString(),
          ...additionalDetails,
        },
        message
      );
    },
    [userId, userEmail, component]
  );

  // Log error with audit trail
  const logError = useCallback(
    async (error: Error, context?: Record<string, any>) => {
      await auditLogger.log(AuditEventType.USER_ACTION, {
        userId,
        userEmail,
        resource: pathname,
        action: 'error',
        success: false,
        errorMessage: error.message,
        details: {
          component,
          errorName: error.name,
          errorStack: error.stack,
          timestamp: new Date().toISOString(),
          ...context,
        },
      });
    },
    [userId, userEmail, pathname, component]
  );

  return {
    logAction,
    logFormSubmit,
    logButtonClick,
    logDataOperation,
    logSecurityIncident,
    logError,
    userId,
    userEmail,
  };
}