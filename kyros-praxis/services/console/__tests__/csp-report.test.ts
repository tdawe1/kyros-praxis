/**
 * Tests for the CSP report endpoint
 * This test verifies that the endpoint properly handles CSP reports
 * and avoids the invalid HTTP 204 with body issue.
 */

import { POST } from '../app/api/security/csp-report/route';
import { NextRequest } from 'next/server';

// Mock fetch globally
global.fetch = jest.fn();

function createMockRequest(body: any) {
  return new NextRequest(new Request('http://localhost:3000/api/security/csp-report', {
    method: 'POST',
    body: JSON.stringify(body),
    headers: {
      'Content-Type': 'application/json',
    },
  }));
}

describe('CSP Report Endpoint', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should return 200 with JSON body for successful CSP report processing', async () => {
    // Mock successful orchestrator response
    (fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'reported' }),
    });

    const mockCSPReport = {
      csp_report: {
        document_uri: 'https://example.com/page',
        violated_directive: 'script-src',
        effective_directive: 'script-src',
        original_policy: "script-src 'self'",
        blocked_uri: 'https://evil.com/malicious.js',
        status_code: 200,
      },
    };

    const request = createMockRequest(mockCSPReport);
    const response = await POST(request);
    const responseBody = await response.json();

    // Verify response status and body
    expect(response.status).toBe(200);
    expect(responseBody).toEqual({ status: 'reported' });

    // Verify the forwarding to orchestrator
    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/security/csp-report',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(mockCSPReport),
      }
    );
  });

  it('should return 400 for invalid CSP report format', async () => {
    const invalidReport = {
      invalid_field: 'invalid_data',
    };

    const request = createMockRequest(invalidReport);
    const response = await POST(request);
    const responseBody = await response.json();

    expect(response.status).toBe(400);
    expect(responseBody).toEqual({ error: 'Invalid CSP report format' });
    expect(fetch).not.toHaveBeenCalled();
  });

  it('should return 500 when orchestrator forwarding fails', async () => {
    // Mock failed orchestrator response
    (fetch as jest.Mock).mockResolvedValue({
      ok: false,
      statusText: 'Internal Server Error',
    });

    const mockCSPReport = {
      csp_report: {
        document_uri: 'https://example.com/page',
        violated_directive: 'script-src',
        effective_directive: 'script-src',
        original_policy: "script-src 'self'",
        blocked_uri: 'https://evil.com/malicious.js',
      },
    };

    const request = createMockRequest(mockCSPReport);
    const response = await POST(request);
    const responseBody = await response.json();

    expect(response.status).toBe(500);
    expect(responseBody).toEqual({ error: 'Failed to process CSP report' });
  });

  it('should handle network errors gracefully', async () => {
    // Mock network error
    (fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

    const mockCSPReport = {
      csp_report: {
        document_uri: 'https://example.com/page',
        violated_directive: 'script-src',
        effective_directive: 'script-src',
        original_policy: "script-src 'self'",
        blocked_uri: 'https://evil.com/malicious.js',
      },
    };

    const request = createMockRequest(mockCSPReport);
    const response = await POST(request);
    const responseBody = await response.json();

    expect(response.status).toBe(500);
    expect(responseBody).toEqual({ error: 'Failed to process CSP report' });
  });

  it('should never return HTTP 204 with a JSON body (the original bug)', async () => {
    // Mock successful orchestrator response
    (fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'reported' }),
    });

    const mockCSPReport = {
      csp_report: {
        document_uri: 'https://example.com/page',
        violated_directive: 'script-src',
        effective_directive: 'script-src',
        original_policy: "script-src 'self'",
        blocked_uri: 'https://evil.com/malicious.js',
      },
    };

    const request = createMockRequest(mockCSPReport);
    const response = await POST(request);
    const responseBody = await response.json();

    // This test specifically verifies we avoid the original bug:
    // NextResponse.json({ status: 'reported' }, { status: 204 })
    // HTTP 204 should never have a body, so we use 200 instead
    expect(response.status).toBe(200);
    expect(responseBody).toEqual({ status: 'reported' });
  });
});