import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { auth } from '@/lib/auth-v5'

// Define protected routes that require authentication
const protectedRoutes = [
  '/agents',
  '/jobs', 
  '/tasks',
  '/dashboard',
  '/settings',
  '/super',
  '/translations',
  '/quotes',
  '/inventory',
  '/marketing',
  '/remote',
  '/assistant',
  '/system',
  '/api/protected' // Protected API routes prefix
]

// Define public routes that don't require authentication
const publicRoutes = [
  '/auth',
  '/auth/login',
  '/auth/register',
  '/api/auth', // NextAuth routes
  '/api/health',
  '/api/sentry-example-api',
  '/_next',
  '/favicon.ico',
  '/static'
]

// Role-based access control mapping
const roleBasedRoutes: Record<string, string[]> = {
  '/system': ['admin', 'super_admin'],
  '/settings/users': ['admin', 'super_admin'],
  '/settings/organization': ['admin', 'super_admin'],
  '/super': ['super_admin']
}

function isProtectedRoute(pathname: string): boolean {
  return protectedRoutes.some(route => pathname.startsWith(route))
}

function isPublicRoute(pathname: string): boolean {
  return publicRoutes.some(route => pathname.startsWith(route))
}

function hasRequiredRole(pathname: string, userRoles: string[] = []): boolean {
  const requiredRoles = roleBasedRoutes[pathname]
  if (!requiredRoles) return true // No specific role required
  
  return requiredRoles.some(role => userRoles.includes(role))
}

export default auth((req: NextRequest & { auth?: any }) => {
  const { pathname } = req.nextUrl
  const session = req.auth

  // Allow public routes
  if (isPublicRoute(pathname)) {
    return NextResponse.next()
  }

  // Redirect to login if accessing protected route without session
  if (isProtectedRoute(pathname) && !session) {
    const loginUrl = new URL('/auth', req.url)
    loginUrl.searchParams.set('callbackUrl', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // Check role-based access for authenticated users
  if (session && isProtectedRoute(pathname)) {
    const userRoles = (session.user as any)?.roles || []
    
    if (!hasRequiredRole(pathname, userRoles)) {
      // Redirect to unauthorized page or main dashboard
      return NextResponse.redirect(new URL('/agents', req.url))
    }
  }

  // Add security headers for all responses
  const response = NextResponse.next()
  
  // Security headers
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')
  response.headers.set('X-XSS-Protection', '1; mode=block')
  
  // Content Security Policy
  const csp = [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.sentry-cdn.com",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data: https:",
    "connect-src 'self' https://o4506953830850560.ingest.us.sentry.io ws: wss:",
    "frame-ancestors 'none'"
  ].join('; ')
  
  response.headers.set('Content-Security-Policy', csp)

  return response
})

// Configure which routes the middleware should run on
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
}