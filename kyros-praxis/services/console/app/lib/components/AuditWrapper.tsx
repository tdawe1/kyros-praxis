/**
 * Wrapper component that adds automatic audit logging to child components
 */

'use client';

import React, { ReactNode, MouseEvent } from 'react';
import { useAuditLogging } from '../../hooks/useAuditLogging';

interface AuditWrapperProps {
  children: ReactNode;
  component?: string;
  trackClicks?: boolean;
  trackForms?: boolean;
  trackPageViews?: boolean;
  logData?: Record<string, any>;
}

export function AuditWrapper({
  children,
  component = 'wrapped-component',
  trackClicks = true,
  trackForms = true,
  trackPageViews = true,
  logData = {},
}: AuditWrapperProps) {
  const { logAction, logFormSubmit, logButtonClick } = useAuditLogging({
    component,
    trackPageViews,
    trackFormSubmissions: trackForms,
    trackButtonClicks: trackClicks,
  });

  const handleClick = async (event: MouseEvent) => {
    if (!trackClicks) return;

    const target = event.target as HTMLElement;
    const tagName = target.tagName.toLowerCase();
    
    // Determine what type of element was clicked
    if (tagName === 'button' || target.getAttribute('role') === 'button') {
      const buttonText = target.textContent?.trim() || target.getAttribute('aria-label') || 'Unknown button';
      const buttonId = target.id || target.getAttribute('data-testid') || 'unknown';
      
      await logButtonClick(buttonId, buttonText, {
        ...logData,
        elementType: 'button',
        tagName,
      });
    } else if (tagName === 'a') {
      const href = target.getAttribute('href');
      await logAction('link_click', {
        ...logData,
        href,
        linkText: target.textContent?.trim(),
        elementType: 'link',
      });
    } else {
      await logAction('element_click', {
        ...logData,
        elementType: tagName,
        elementText: target.textContent?.trim()?.slice(0, 50),
      });
    }
  };

  const handleFormSubmit = async (event: React.FormEvent) => {
    if (!trackForms) return;

    const form = event.target as HTMLFormElement;
    const formName = form.getAttribute('name') || form.id || 'unnamed-form';
    
    // Get form data (excluding sensitive fields)
    const formData = new FormData(form);
    const sanitizedData: Record<string, string> = {};
    
    for (const [key, value] of formData.entries()) {
      // Don't log sensitive field values
      const isSensitive = /password|secret|token|key|ssn|credit|card/i.test(key);
      sanitizedData[key] = isSensitive ? '[REDACTED]' : String(value).slice(0, 100);
    }

    await logFormSubmit(formName, {
      ...logData,
      fieldCount: formData.keys.length,
      hasFileUpload: Array.from(formData.values()).some(v => v instanceof File),
    });
  };

  // Wrap children with event handlers
  const wrappedChildren = React.cloneElement(
    React.Children.only(children) as React.ReactElement,
    {
      onClick: (event: MouseEvent) => {
        // Call original onClick if it exists
        const originalOnClick = (children as React.ReactElement).props.onClick;
        if (originalOnClick) originalOnClick(event);
        
        // Add our audit logging
        handleClick(event);
      },
      onSubmit: (event: React.FormEvent) => {
        // Call original onSubmit if it exists
        const originalOnSubmit = (children as React.ReactElement).props.onSubmit;
        if (originalOnSubmit) originalOnSubmit(event);
        
        // Add our audit logging
        handleFormSubmit(event);
      },
    }
  );

  return wrappedChildren;
}

/**
 * Higher-order component for adding audit logging to any component
 */
export function withAuditLogging<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  auditConfig: Omit<AuditWrapperProps, 'children'> = {}
) {
  const displayName = WrappedComponent.displayName || WrappedComponent.name || 'Component';
  
  const AuditedComponent = (props: P) => {
    return (
      <AuditWrapper {...auditConfig} component={displayName.toLowerCase()}>
        <WrappedComponent {...props} />
      </AuditWrapper>
    );
  };

  AuditedComponent.displayName = `withAuditLogging(${displayName})`;
  return AuditedComponent;
}

/**
 * Hook for manually logging specific audit events within components
 */
export function useManualAuditLogging() {
  const { logAction, logDataOperation, logSecurityIncident, logError } = useAuditLogging();

  return {
    logAction,
    logDataOperation,
    logSecurityIncident,
    logError,
  };
}