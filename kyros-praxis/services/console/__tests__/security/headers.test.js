/**
 * Security Headers Test Suite
 * 
 * Tests to validate that all required security headers are properly configured
 * in the Next.js application as per the security requirements.
 */

import nextConfig from '../../next.config.js';

describe('Security Headers Configuration', () => {
  let headers;

  beforeAll(async () => {
    // Get headers from Next.js config
    if (nextConfig.headers) {
      const headersConfig = await nextConfig.headers();
      headers = headersConfig.find(config => config.source === '/:path*')?.headers || [];
    }
  });

  test('should have Content Security Policy (CSP) headers', () => {
    const cspHeader = headers.find(h => h.key === 'Content-Security-Policy');
    expect(cspHeader).toBeDefined();
    expect(cspHeader.value).toBeTruthy();
    
    // CSP should include basic security directives
    expect(cspHeader.value).toMatch(/default-src\s+'self'/);
    expect(cspHeader.value).toMatch(/frame-ancestors\s+'none'/);
    expect(cspHeader.value).toMatch(/base-uri\s+'self'/);
    expect(cspHeader.value).toMatch(/form-action\s+'self'/);
  });

  test('should have XSS protection headers', () => {
    const xssHeader = headers.find(h => h.key === 'X-XSS-Protection');
    expect(xssHeader).toBeDefined();
    expect(xssHeader.value).toBe('1; mode=block');
  });

  test('should have HSTS (HTTP Strict Transport Security) headers', () => {
    const hstsHeader = headers.find(h => h.key === 'Strict-Transport-Security');
    expect(hstsHeader).toBeDefined();
    expect(hstsHeader.value).toMatch(/max-age=\d+/);
    expect(hstsHeader.value).toMatch(/includeSubDomains/);
  });

  test('should have Frame options for clickjacking protection', () => {
    const frameHeader = headers.find(h => h.key === 'X-Frame-Options');
    expect(frameHeader).toBeDefined();
    // Should be either DENY, SAMEORIGIN, or ALLOW-FROM
    expect(['DENY', 'SAMEORIGIN'].includes(frameHeader.value) || 
           frameHeader.value.startsWith('ALLOW-FROM')).toBe(true);
  });

  test('should have Referrer policy configured', () => {
    const referrerHeader = headers.find(h => h.key === 'Referrer-Policy');
    expect(referrerHeader).toBeDefined();
    expect(referrerHeader.value).toBeTruthy();
    
    // Common secure referrer policies
    const validPolicies = [
      'strict-origin-when-cross-origin',
      'strict-origin',
      'same-origin',
      'no-referrer'
    ];
    expect(validPolicies.includes(referrerHeader.value)).toBe(true);
  });

  test('should have Feature/Permissions policy headers', () => {
    const permissionsHeader = headers.find(h => h.key === 'Permissions-Policy');
    expect(permissionsHeader).toBeDefined();
    expect(permissionsHeader.value).toBeTruthy();
    
    // Should restrict sensitive features
    expect(permissionsHeader.value).toMatch(/camera=\(\)/);
    expect(permissionsHeader.value).toMatch(/microphone=\(\)/);
    expect(permissionsHeader.value).toMatch(/geolocation=\(\)/);
  });

  test('should have Content-Type-Options header', () => {
    const ctHeader = headers.find(h => h.key === 'X-Content-Type-Options');
    expect(ctHeader).toBeDefined();
    expect(ctHeader.value).toBe('nosniff');
  });

  test('should disable X-Powered-By header', () => {
    // This is tested via nextConfig.poweredByHeader
    expect(nextConfig.poweredByHeader).toBe(false);
  });

  test('CSP should be environment-aware', () => {
    // Test both development and production CSP configurations
    const cspHeader = headers.find(h => h.key === 'Content-Security-Policy');
    
    if (process.env.NODE_ENV === 'development') {
      // Development should allow unsafe-eval for Next.js
      expect(cspHeader.value).toMatch(/'unsafe-eval'/);
      expect(cspHeader.value).toMatch(/localhost/);
    } else {
      // Production should be more restrictive
      expect(cspHeader.value).not.toMatch(/'unsafe-eval'/);
      expect(cspHeader.value).toMatch(/upgrade-insecure-requests/);
    }
  });
});

describe('Security Headers Values Validation', () => {
  test('CSP directives should be properly formatted', async () => {
    if (!nextConfig.headers) return;
    
    const headersConfig = await nextConfig.headers();
    const headers = headersConfig.find(config => config.source === '/:path*')?.headers || [];
    const cspHeader = headers.find(h => h.key === 'Content-Security-Policy');
    
    if (cspHeader) {
      // Split CSP into directives
      const directives = cspHeader.value.split(';').map(d => d.trim());
      
      // Check for common directives
      const hasDefaultSrc = directives.some(d => d.startsWith('default-src'));
      const hasScriptSrc = directives.some(d => d.startsWith('script-src'));
      const hasStyleSrc = directives.some(d => d.startsWith('style-src'));
      const hasFrameAncestors = directives.some(d => d.startsWith('frame-ancestors'));
      
      expect(hasDefaultSrc).toBe(true);
      expect(hasFrameAncestors).toBe(true);
      
      // Validate that directive values are not empty
      directives.forEach(directive => {
        if (directive.trim()) {
          // CSP directives should either have sources or be standalone keywords
          const standaloneKeywords = ['upgrade-insecure-requests', 'block-all-mixed-content'];
          if (!standaloneKeywords.includes(directive.trim())) {
            expect(directive).toMatch(/^\w+(-\w+)*\s+/);
          }
        }
      });
    }
  });

  test('HSTS should have appropriate max-age', async () => {
    if (!nextConfig.headers) return;
    
    const headersConfig = await nextConfig.headers();
    const headers = headersConfig.find(config => config.source === '/:path*')?.headers || [];
    const hstsHeader = headers.find(h => h.key === 'Strict-Transport-Security');
    
    if (hstsHeader) {
      const maxAgeMatch = hstsHeader.value.match(/max-age=(\d+)/);
      if (maxAgeMatch) {
        const maxAge = parseInt(maxAgeMatch[1], 10);
        // Should be at least 1 year (31536000 seconds)
        expect(maxAge).toBeGreaterThanOrEqual(31536000);
      }
    }
  });
});