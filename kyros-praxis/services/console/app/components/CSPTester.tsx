'use client';

import { Button } from '@carbon/react';
import { testCSPViolation } from '@/lib/csp-violation-report';

/**
 * CSP Testing Component (Development Only)
 * 
 * Provides buttons to test CSP violations in development mode.
 * This component only renders in development environments.
 */
export function CSPTester() {
  // Only show in development
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <div style={{ 
      position: 'fixed', 
      bottom: '20px', 
      right: '20px', 
      zIndex: 9999,
      background: '#f4f4f4',
      padding: '10px',
      border: '1px solid #ccc',
      borderRadius: '4px',
      fontSize: '12px'
    }}>
      <div style={{ marginBottom: '10px', fontWeight: 'bold' }}>
        CSP Testing (Dev Only)
      </div>
      <Button
        size="sm"
        kind="secondary"
        onClick={testCSPViolation}
      >
        Test CSP Violation
      </Button>
    </div>
  );
}