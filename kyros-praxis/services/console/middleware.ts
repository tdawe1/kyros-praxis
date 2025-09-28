import { auth } from "@/lib/auth-v5"
import { NextResponse } from "next/server"

export default auth((req) => {
  const { nextUrl } = req
  const isLoggedIn = !!req.auth

  // Public routes that don't require authentication
  const isPublicRoute = [
    '/auth',
    '/auth/login',
    '/api/auth',
    '/health',
    '/monitoring'
  ].some(path => nextUrl.pathname.startsWith(path))

  // API routes for NextAuth
  const isAuthApiRoute = nextUrl.pathname.startsWith('/api/auth')

  // Allow auth API routes
  if (isAuthApiRoute) {
    return NextResponse.next()
  }

  // Allow public routes
  if (isPublicRoute) {
    return NextResponse.next()
  }

  // Redirect to login if not authenticated and trying to access protected route
  if (!isLoggedIn) {
    const callbackUrl = nextUrl.pathname + nextUrl.search
    const loginUrl = new URL('/auth', nextUrl.origin)
    loginUrl.searchParams.set('callbackUrl', callbackUrl)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
})

// Configure which routes should be processed by middleware
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.png$|.*\\.jpg$|.*\\.jpeg$|.*\\.gif$|.*\\.svg$).*)',
  ],
}