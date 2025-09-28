/**
 * Next.js middleware for automatic audit logging
 * 
 * This middleware automatically tracks:
 * - Authentication events
 * - Route access attempts
 * - Security-related events
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getToken } from 'next-auth/jwt';

// Paths that require authentication
const protectedPaths = [
  '/dashboard',
  '/agents',
  '/tasks',
  '/settings',
  '/admin',
  '/api/agents',
  '/api/tasks',
  '/api/settings',
];

// Admin-only paths
const adminPaths = [
  '/admin',
  '/api/admin',
  '/settings/admin',
];

// Utility to get client IP
function getClientIP(request: NextRequest): string {
  const forwarded = request.headers.get('x-forwarded-for');
  const realIP = request.headers.get('x-real-ip');
  
  if (forwarded) {
    return forwarded.split(',')[0].trim();
  }
  
  return realIP || 'unknown';
}

// Utility to check if path matches patterns
function matchesPath(url: string, patterns: string[]): boolean {
  return patterns.some(pattern => url.startsWith(pattern));
}

// Log audit event to API (non-blocking)
async function logAuditEvent(
  eventType: string,
  request: NextRequest,
  userId?: string,
  userEmail?: string,
  success = true,
  errorMessage?: string,
  additionalDetails?: Record<string, any>
) {
  try {
    // Create audit log entry
    const auditEntry = {
      id: `audit_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      eventType,
      severity: eventType.includes('security') ? 'high' : 
               eventType.includes('auth') ? 'medium' : 'low',
      userId,
      userEmail,
      ipAddress: getClientIP(request),
      userAgent: request.headers.get('user-agent'),
      resource: request.url,
      action: request.method.toLowerCase(),
      success,
      errorMessage,
      details: {
        path: request.nextUrl.pathname,
        method: request.method,
        timestamp: new Date().toISOString(),
        ...additionalDetails,
      },
    };

    // Send to audit API (non-blocking)
    fetch(`${request.nextUrl.origin}/api/audit/logs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ logs: [auditEntry] }),
    }).catch(error => {
      console.error('Failed to send audit log:', error);
    });

  } catch (error) {
    console.error('Error creating audit log:', error);
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Skip audit logging for static assets and internal API calls
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/favicon') ||
    pathname.includes('.') && !pathname.includes('/api/')
  ) {
    return NextResponse.next();
  }

  try {
    // Get session token
    const token = await getToken({
      req: request,
      secret: process.env.NEXTAUTH_SECRET,
    });

    const userId = token?.sub || token?.id || undefined;
    const userEmail = token?.email || undefined;
    const isAuthenticated = !!token;

    // Check if accessing protected path
    const isProtectedPath = matchesPath(pathname, protectedPaths);
    const isAdminPath = matchesPath(pathname, adminPaths);

    // Log route access attempt
    await logAuditEvent(
      'user.page.access',
      request,
      userId,
      userEmail,
      true,
      undefined,
      {
        isProtectedPath,
        isAdminPath,
        isAuthenticated,
      }
    );

    // Handle unauthenticated access to protected routes
    if (isProtectedPath && !isAuthenticated) {
      await logAuditEvent(
        'security.unauthorized.access',
        request,
        undefined,
        undefined,
        false,
        'Attempted to access protected route without authentication',
        {
          attemptedPath: pathname,
          redirectedTo: '/auth',
        }
      );

      // Redirect to auth page
      const authUrl = new URL('/auth', request.url);
      authUrl.searchParams.set('callbackUrl', pathname);
      return NextResponse.redirect(authUrl);
    }

    // Handle admin path access
    if (isAdminPath && isAuthenticated) {
      const isAdmin = token?.role === 'admin' || token?.isAdmin;
      
      if (!isAdmin) {
        await logAuditEvent(
          'security.permission.denied',
          request,
          userId,
          userEmail,
          false,
          'Attempted to access admin area without admin privileges',
          {
            attemptedPath: pathname,
            userRole: token?.role,
          }
        );

        // Redirect to dashboard or show 403
        return NextResponse.redirect(new URL('/dashboard', request.url));
      }

      // Log admin area access
      await logAuditEvent(
        'admin.area.access',
        request,
        userId,
        userEmail,
        true,
        undefined,
        {
          adminPath: pathname,
        }
      );
    }

    // Log successful authentication events
    if (pathname === '/auth' && isAuthenticated) {
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }

    // Rate limiting for API endpoints (basic implementation)
    if (pathname.startsWith('/api/')) {
      const clientIP = getClientIP(request);
      // Implementation would check against rate limit store
      // For now, just log API access
      await logAuditEvent(
        'api.access',
        request,
        userId,
        userEmail,
        true,
        undefined,
        {
          endpoint: pathname,
          clientIP,
        }
      );
    }

    return NextResponse.next();

  } catch (error) {
    console.error('Middleware error:', error);
    
    // Log middleware error as security incident
    await logAuditEvent(
      'security.middleware.error',
      request,
      undefined,
      undefined,
      false,
      error instanceof Error ? error.message : 'Unknown middleware error',
      {
        errorType: error instanceof Error ? error.name : 'Unknown',
      }
    );

    return NextResponse.next();
  }
}

// Configure which routes this middleware should run on
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};