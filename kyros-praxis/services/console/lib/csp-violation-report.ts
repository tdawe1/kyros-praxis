/**
 * CSP Violation Reporting Utility
 * 
 * Provides client-side handling of Content Security Policy violations.
 * Automatically reports violations to the backend for security monitoring.
 */

export interface CSPViolationEvent {
  documentURI: string;
  violatedDirective: string;
  effectiveDirective: string;
  originalPolicy: string;
  blockedURI: string;
  statusCode: number;
  lineNumber?: number;
  columnNumber?: number;
  sourceFile?: string;
}

/**
 * Report CSP violation to backend endpoint
 */
async function reportCSPViolation(violation: CSPViolationEvent) {
  try {
    // Use the local API route which forwards to orchestrator
    const apiUrl = '/api/v1/security/csp-report';

    await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        csp_report: {
          document_uri: violation.documentURI,
          violated_directive: violation.violatedDirective,
          effective_directive: violation.effectiveDirective,
          original_policy: violation.originalPolicy,
          blocked_uri: violation.blockedURI,
          status_code: violation.statusCode || 0,
        },
      }),
    });
  } catch (error) {
    console.error('Failed to report CSP violation:', error);
  }
}

/**
 * Initialize CSP violation reporting
 * Call this in your root layout or app component
 */
export function initCSPViolationReporting() {
  if (typeof document !== 'undefined') {
    document.addEventListener('securitypolicyviolation', (event) => {
      const violation: CSPViolationEvent = {
        documentURI: event.documentURI,
        violatedDirective: event.violatedDirective,
        effectiveDirective: event.effectiveDirective,
        originalPolicy: event.originalPolicy,
        blockedURI: event.blockedURI,
        statusCode: event.statusCode,
        lineNumber: event.lineNumber,
        columnNumber: event.columnNumber,
        sourceFile: event.sourceFile,
      };

      // Report to backend
      reportCSPViolation(violation);

      // Also log to console for development
      if (process.env.NODE_ENV === 'development') {
        console.warn('CSP Violation:', violation);
      }
    });
  }
}

/**
 * Test CSP policy by intentionally triggering a violation (development only)
 */
export function testCSPViolation() {
  if (process.env.NODE_ENV === 'development' && typeof document !== 'undefined') {
    console.log('Testing CSP violation reporting...');
    
    // Create a script tag that should violate CSP (inline script without nonce)
    const testScript = document.createElement('script');
    testScript.textContent = 'console.log("CSP test violation");';
    document.head.appendChild(testScript);
    
    // Remove it immediately
    setTimeout(() => {
      document.head.removeChild(testScript);
    }, 100);
  }
}