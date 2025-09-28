// middleware.ts - Next.js middleware for CSP nonce generation
import { NextRequest, NextResponse } from 'next/server';

// Generate a cryptographically secure nonce
function generateNonce(): string {
  // Use Web Crypto API in edge runtime
  if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
    const array = new Uint8Array(16);
    crypto.getRandomValues(array);
    return btoa(String.fromCharCode(...array)).replace(/[+/=]/g, '');
  }
  
  // Fallback for older environments
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

export function middleware(request: NextRequest) {
  // Generate a unique nonce for this request
  const nonce = generateNonce();
  
  // Create response
  const response = NextResponse.next();
  
  // Add nonce to request headers for use in layout/components
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set('x-nonce', nonce);
  
  return NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  });
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - monitoring (Sentry tunnel)
     */
    '/((?!api|_next/static|_next/image|favicon.ico|monitoring).*)',
  ],
};