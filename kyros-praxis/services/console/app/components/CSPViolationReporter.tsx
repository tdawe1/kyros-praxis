'use client';

import { useEffect } from 'react';
import { initCSPViolationReporting } from '@/lib/csp-violation-report';

/**
 * CSP Violation Reporter Component
 * 
 * Initializes client-side CSP violation reporting when the component mounts.
 * This should be included in the root layout to ensure violations are captured
 * across the entire application.
 */
export function CSPViolationReporter() {
  useEffect(() => {
    // Initialize CSP violation reporting
    initCSPViolationReporting();
  }, []);

  // This component doesn't render anything
  return null;
}