/**
 * Security middleware for input sanitization and protection
 */

import { NextRequest, NextResponse } from 'next/server';
import { sanitizeText } from './app/lib/sanitization';

/**
 * Rate limiting storage (in production, use Redis or database)
 */
const rateLimitStore = new Map<string, { count: number; resetTime: number }>();

/**
 * Clean up expired rate limit entries
 */
function cleanupRateLimit() {
  const now = Date.now();
  for (const [key, value] of rateLimitStore.entries()) {
    if (now > value.resetTime) {
      rateLimitStore.delete(key);
    }
  }
}

/**
 * Rate limiting middleware
 */
function rateLimit(request: NextRequest): boolean {
  const ip = request.ip || request.headers.get('x-forwarded-for') || 'unknown';
  const key = `ratelimit:${ip}`;
  const now = Date.now();
  const windowMs = 15 * 60 * 1000; // 15 minutes
  const maxRequests = 1000; // Requests per window

  // Clean up expired entries periodically
  if (Math.random() < 0.01) { // 1% chance
    cleanupRateLimit();
  }

  const record = rateLimitStore.get(key);
  
  if (!record || now > record.resetTime) {
    rateLimitStore.set(key, { count: 1, resetTime: now + windowMs });
    return true;
  }

  if (record.count >= maxRequests) {
    return false;
  }

  record.count++;
  return true;
}

/**
 * Sanitize URL parameters
 */
function sanitizeUrlParams(url: URL): URL {
  const sanitizedUrl = new URL(url);
  
  // Clear existing search params
  sanitizedUrl.search = '';
  
  // Sanitize each parameter
  for (const [key, value] of url.searchParams.entries()) {
    const sanitizedKey = sanitizeText(key);
    const sanitizedValue = sanitizeText(value);
    
    // Only add if both key and value are valid after sanitization
    if (sanitizedKey && sanitizedValue) {
      sanitizedUrl.searchParams.set(sanitizedKey, sanitizedValue);
    }
  }
  
  return sanitizedUrl;
}

/**
 * Security headers middleware
 */
function addSecurityHeaders(response: NextResponse): NextResponse {
  // Add nonce for CSP (would be generated per request in production)
  const nonce = Buffer.from(crypto.getRandomValues(new Uint8Array(16))).toString('base64');
  
  // Additional security headers
  response.headers.set('X-Robots-Tag', 'noindex, nofollow');
  response.headers.set('X-Frame-Options', 'SAMEORIGIN');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('X-XSS-Protection', '1; mode=block');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  
  // Add CSP nonce to response for dynamic script execution
  response.headers.set('X-CSP-Nonce', nonce);
  
  return response;
}

/**
 * Main middleware function
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip middleware for static assets and Next.js internals
  if (
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/api/_') ||
    pathname.startsWith('/favicon.') ||
    pathname.endsWith('.ico') ||
    pathname.endsWith('.png') ||
    pathname.endsWith('.jpg') ||
    pathname.endsWith('.jpeg') ||
    pathname.endsWith('.gif') ||
    pathname.endsWith('.svg') ||
    pathname.endsWith('.css') ||
    pathname.endsWith('.js') ||
    pathname.endsWith('.map')
  ) {
    return NextResponse.next();
  }

  // Rate limiting
  if (!rateLimit(request)) {
    return new NextResponse('Too Many Requests', { 
      status: 429,
      headers: {
        'Retry-After': '900', // 15 minutes
        'Content-Type': 'text/plain'
      }
    });
  }

  // Sanitize URL parameters for GET requests
  if (request.method === 'GET' && request.nextUrl.search) {
    const sanitizedUrl = sanitizeUrlParams(request.nextUrl);
    
    // If URL parameters were modified, redirect to sanitized version
    if (sanitizedUrl.search !== request.nextUrl.search) {
      return NextResponse.redirect(sanitizedUrl);
    }
  }

  // Validate Content-Type for POST/PUT/PATCH requests
  if (['POST', 'PUT', 'PATCH'].includes(request.method)) {
    const contentType = request.headers.get('content-type');
    
    // For API routes, require JSON content type
    if (pathname.startsWith('/api/')) {
      if (!contentType || !contentType.includes('application/json')) {
        return new NextResponse(
          JSON.stringify({ error: 'Content-Type must be application/json' }),
          { 
            status: 400,
            headers: { 'Content-Type': 'application/json' }
          }
        );
      }
    }
    
    // Validate request size
    const contentLength = request.headers.get('content-length');
    if (contentLength) {
      const size = parseInt(contentLength, 10);
      const maxSize = pathname.startsWith('/api/upload') ? 50 * 1024 * 1024 : 1024 * 1024; // 50MB for uploads, 1MB for others
      
      if (size > maxSize) {
        return new NextResponse(
          JSON.stringify({ error: 'Request too large' }),
          { 
            status: 413,
            headers: { 'Content-Type': 'application/json' }
          }
        );
      }
    }
  }

  // Block potentially dangerous paths
  const dangerousPaths = [
    '/.env',
    '/.git',
    '/wp-admin',
    '/admin',
    '/phpmyadmin',
    '/.htaccess',
    '/web.config'
  ];

  if (dangerousPaths.some(path => pathname.startsWith(path))) {
    return new NextResponse('Not Found', { status: 404 });
  }

  // Continue with request and add security headers to response
  const response = NextResponse.next();
  return addSecurityHeaders(response);
}

/**
 * Middleware configuration
 */
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