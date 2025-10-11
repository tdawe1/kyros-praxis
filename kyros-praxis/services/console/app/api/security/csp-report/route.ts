import { NextRequest, NextResponse } from 'next/server';

/**
 * CSP Report forwarding endpoint
 * 
 * This endpoint receives Content Security Policy (CSP) violation reports
 * from browsers and forwards them to the orchestrator service for processing.
 * 
 * The endpoint properly handles the response by either:
 * - Returning a 200 status with JSON body for successful forwarding
 * - Returning an empty 204 response without body
 * 
 * This fixes the issue where NextResponse.json({ status: 'reported' }, { status: 204 })
 * was being used, which is invalid because HTTP 204 status cannot have a body.
 */

interface CSPReport {
  document_uri: string;
  violated_directive: string;
  effective_directive: string;
  original_policy: string;
  blocked_uri: string;
  status_code?: number;
}

interface CSPReportData {
  csp_report: CSPReport;
}

export async function POST(req: NextRequest) {
  try {
    const reportData: CSPReportData = await req.json();
    
    // Validate the CSP report structure
    if (!reportData.csp_report) {
      return NextResponse.json(
        { error: 'Invalid CSP report format' },
        { status: 400 }
      );
    }

    // Forward to orchestrator service
    const orchestratorUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const forwardUrl = `${orchestratorUrl}/api/v1/security/csp-report`;

    const response = await fetch(forwardUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(reportData),
    });

    if (!response.ok) {
      console.error('Failed to forward CSP report to orchestrator:', response.statusText);
      return NextResponse.json(
        { error: 'Failed to process CSP report' },
        { status: 500 }
      );
    }

    // Return 200 with JSON body (not 204 with body which is invalid)
    return NextResponse.json({ status: 'reported' });

  } catch (error) {
    console.error('Error processing CSP report:', error);
    return NextResponse.json(
      { error: 'Failed to process CSP report' },
      { status: 500 }
    );
  }
}