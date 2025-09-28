import { NextRequest, NextResponse } from 'next/server';

/**
 * CSP Violation Report Handler for Frontend
 * 
 * This API route receives CSP violations from the browser and forwards them
 * to the orchestrator service for centralized security monitoring.
 */

interface CSPReport {
  document_uri: string;
  violated_directive: string;
  effective_directive: string;
  original_policy: string;
  blocked_uri: string;
  status_code: number;
}

interface CSPReportData {
  csp_report: CSPReport;
}

export async function POST(request: NextRequest) {
  try {
    const reportData: CSPReportData = await request.json();
    
    // Get orchestrator URL from environment
    const orchestratorUrl = process.env.ORCHESTRATOR_URL || 'http://localhost:8000';
    const reportEndpoint = `${orchestratorUrl}/api/v1/security/csp-report`;
    
    // Forward the report to the orchestrator service
    const response = await fetch(reportEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Forward client IP if available
        'X-Forwarded-For': request.headers.get('x-forwarded-for') || request.ip || 'unknown',
        'User-Agent': request.headers.get('user-agent') || 'kyros-console',
      },
      body: JSON.stringify(reportData),
    });

    if (!response.ok) {
      console.error('Failed to forward CSP report to orchestrator:', response.statusText);
    }

    // Return success response to browser
    return NextResponse.json({ status: 'reported' }, { status: 204 });
    
  } catch (error) {
    console.error('Error processing CSP report:', error);
    
    // Log the violation locally as fallback
    console.warn('CSP Violation (fallback logging):', {
      timestamp: new Date().toISOString(),
      client_ip: request.headers.get('x-forwarded-for') || request.ip || 'unknown',
      user_agent: request.headers.get('user-agent') || 'unknown',
      error: error instanceof Error ? error.message : 'Unknown error',
    });
    
    return NextResponse.json(
      { error: 'Failed to process CSP report' },
      { status: 500 }
    );
  }
}