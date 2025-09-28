/**
 * API endpoint for receiving and processing audit logs
 */

import { NextRequest, NextResponse } from 'next/server';
import { AuditLogEntry } from '../../../lib/audit';

// Rate limiting (simple in-memory implementation)
const rateLimitMap = new Map<string, { count: number; resetTime: number }>();
const RATE_LIMIT = 100; // requests per minute
const RATE_LIMIT_WINDOW = 60 * 1000; // 1 minute

function checkRateLimit(identifier: string): boolean {
  const now = Date.now();
  const record = rateLimitMap.get(identifier);

  if (!record || now > record.resetTime) {
    rateLimitMap.set(identifier, { count: 1, resetTime: now + RATE_LIMIT_WINDOW });
    return true;
  }

  if (record.count >= RATE_LIMIT) {
    return false;
  }

  record.count++;
  return true;
}

function getClientIP(request: NextRequest): string {
  const forwarded = request.headers.get('x-forwarded-for');
  const realIP = request.headers.get('x-real-ip');
  const remoteAddr = request.headers.get('x-remote-addr');
  
  if (forwarded) {
    return forwarded.split(',')[0].trim();
  }
  
  return realIP || remoteAddr || 'unknown';
}

export async function POST(request: NextRequest) {
  try {
    // Get client IP for rate limiting and logging
    const clientIP = getClientIP(request);
    
    // Check rate limit
    if (!checkRateLimit(clientIP)) {
      console.warn(`Rate limit exceeded for IP: ${clientIP}`);
      return NextResponse.json(
        { error: 'Rate limit exceeded' },
        { status: 429 }
      );
    }

    // Parse request body
    const body = await request.json();
    const { logs } = body;

    if (!Array.isArray(logs)) {
      return NextResponse.json(
        { error: 'Invalid request body. Expected logs array.' },
        { status: 400 }
      );
    }

    // Get session for additional context (simplified for now)
    // const session = await getServerSession();
    
    // Enrich logs with server-side information
    const enrichedLogs: AuditLogEntry[] = logs.map((log: AuditLogEntry) => ({
      ...log,
      ipAddress: clientIP,
      // sessionId: session?.user?.id,
      metadata: {
        ...log.metadata,
        serverTimestamp: new Date().toISOString(),
        userAgent: request.headers.get('user-agent') || undefined,
      },
    }));

    // In a real application, you would:
    // 1. Validate log entries
    // 2. Store logs in a database (e.g., PostgreSQL, MongoDB)
    // 3. Send to log aggregation service (e.g., ELK stack, Splunk)
    // 4. Trigger alerts for high-severity events

    // For now, log to console and basic validation
    for (const logEntry of enrichedLogs) {
      // Validate required fields
      if (!logEntry.id || !logEntry.timestamp || !logEntry.eventType) {
        console.error('Invalid audit log entry:', logEntry);
        continue;
      }

      // Log based on severity
      if (logEntry.severity === 'critical' || logEntry.severity === 'high') {
        console.error('[AUDIT-HIGH]', JSON.stringify(logEntry, null, 2));
      } else {
        console.log('[AUDIT]', JSON.stringify(logEntry, null, 2));
      }

      // Trigger alerts for security incidents
      if (logEntry.eventType.startsWith('security.')) {
        console.warn('[SECURITY-ALERT]', {
          eventType: logEntry.eventType,
          userId: logEntry.userId,
          ipAddress: logEntry.ipAddress,
          timestamp: logEntry.timestamp,
          details: logEntry.details,
        });
        
        // In production, send to security monitoring system
        // await sendSecurityAlert(logEntry);
      }
    }

    // Store logs (placeholder for database integration)
    // In a real implementation:
    // await storeAuditLogs(enrichedLogs);
    
    console.log(`Processed ${enrichedLogs.length} audit log entries from ${clientIP}`);

    return NextResponse.json({
      success: true,
      processed: enrichedLogs.length,
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    console.error('Error processing audit logs:', error);
    
    return NextResponse.json(
      { 
        error: 'Internal server error',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

// Handle unsupported methods
export async function GET() {
  return NextResponse.json(
    { error: 'Method not allowed' },
    { status: 405 }
  );
}

export async function PUT() {
  return NextResponse.json(
    { error: 'Method not allowed' },
    { status: 405 }
  );
}

export async function DELETE() {
  return NextResponse.json(
    { error: 'Method not allowed' },
    { status: 405 }
  );
}