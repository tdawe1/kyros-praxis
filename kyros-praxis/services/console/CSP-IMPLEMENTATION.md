# Content Security Policy (CSP) Implementation

## Overview

This document describes the comprehensive CSP implementation for the Kyros Console service, providing enhanced security against XSS attacks and content injection vulnerabilities.

## Implementation Details

### 1. CSP Configuration (`next.config.js`)

**Development Environment:**
```javascript
[
  "default-src 'self'",
  "script-src 'self' 'unsafe-eval' 'unsafe-inline'", // Required for Next.js dev and Sentry
  "style-src 'self' 'unsafe-inline'", // Required for Carbon Design System
  "img-src 'self' data: blob: https:",
  "font-src 'self' data:",
  "connect-src 'self' http://localhost:* ws://localhost:* https://o4506912905486336.ingest.us.sentry.io",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "report-uri /api/v1/security/csp-report",
].join('; ')
```

**Production Environment:**
```javascript
[
  "default-src 'self'",
  "script-src 'self'",
  "style-src 'self'",
  "img-src 'self' data: https:",
  "font-src 'self' data:",
  "connect-src 'self' https://*.kyros-praxis.com wss://*.kyros-praxis.com https://o4506912905486336.ingest.us.sentry.io",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "upgrade-insecure-requests",
  "report-uri /api/v1/security/csp-report",
].join('; ')
```

### 2. Nonce Infrastructure

**Middleware (`middleware.ts`):**
- Generates cryptographically secure nonces for each request
- Uses Web Crypto API for secure random number generation
- Passes nonce via custom headers to components

**Nonce Utilities (`lib/nonce.ts`):**
- `getNonce()`: Retrieves the CSP nonce for the current request
- `getScriptSrcWithNonce()`: Generates script-src directive with nonce
- `getStyleSrcWithNonce()`: Generates style-src directive with nonce

### 3. CSP Violation Reporting

**Client-side Reporter (`lib/csp-violation-report.ts`):**
- Automatically captures `securitypolicyviolation` events
- Reports violations to backend via `/api/v1/security/csp-report`
- Provides testing utilities for development

**Frontend API Route (`app/api/v1/security/csp-report/route.ts`):**
- Receives CSP violations from browser
- Forwards reports to orchestrator service
- Provides fallback logging if orchestrator unavailable

**Reporter Component (`app/components/CSPViolationReporter.tsx`):**
- Initializes violation reporting on app startup
- Included in root layout for global coverage

### 4. Development Testing

**CSP Tester Component (`app/components/CSPTester.tsx`):**
- Development-only component for testing CSP policies
- Provides button to intentionally trigger CSP violations
- Visible in bottom-right corner during development

## Security Benefits

### 1. XSS Prevention
- Prevents execution of unauthorized scripts
- Blocks inline scripts without proper nonces
- Restricts script sources to trusted domains

### 2. Content Injection Protection
- Controls allowed sources for styles, fonts, and images
- Prevents data exfiltration via unauthorized connections
- Blocks malicious frame embedding

### 3. Monitoring & Alerting
- Real-time violation reporting to backend
- Centralized security event logging
- Development-time policy validation

### 4. Environment-Specific Policies
- Stricter policies in production
- Development-friendly policies for testing
- Proper Sentry integration for monitoring

## Configuration Details

### Allowed Sources

**Scripts:** Self-hosted only (production), includes development tools (dev)
**Styles:** Self-hosted, required for Carbon Design System
**Images:** Self, data URLs, HTTPS domains
**Fonts:** Self-hosted, data URLs
**Connections:** Self, Kyros domains, Sentry monitoring
**Frames:** None allowed (prevents clickjacking)

### Reporting

- **Development:** Reports to `/api/v1/security/csp-report`
- **Production:** Reports to `/api/v1/security/csp-report`
- **Backend Integration:** Forwards to orchestrator service
- **Fallback:** Local console logging if backend unavailable

## Testing & Validation

### Manual Testing
1. Start development server: `npm run dev`
2. Navigate to http://localhost:3000
3. Click "Test CSP Violation" button in bottom-right corner
4. Verify violation is reported in console
5. Check network tab for CSP report POST request

### Automated Testing
- Linting: `npm run lint` ✓
- Build validation: `npm run build` (with known unrelated issues)
- Development server: `npm run dev` ✓

## Future Enhancements

1. **Nonce-based Inline Styles:** Implement nonce support for dynamic styles
2. **Report Analysis:** Add CSP violation analytics dashboard
3. **Policy Refinement:** Further restrict policies based on usage patterns
4. **Hash-based CSP:** Consider SHA-256 hashes for known inline content

## Troubleshooting

### Common Issues

1. **Blocked Resources:** Check if source is allowed in CSP policy
2. **Inline Scripts Blocked:** Ensure proper nonce implementation
3. **Font Loading Issues:** Verify font sources in CSP configuration
4. **Development Tools:** Ensure dev environment has appropriate permissions

### Debug Mode

Enable CSP testing component in development to validate policies and test violation reporting functionality.