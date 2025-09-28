import { NextRequest, NextResponse } from 'next/server';
import { withApiAuth, AuthenticatedRequest, rateLimit } from '@/lib/api-auth';

// Example protected API route
async function handleProtected(req: AuthenticatedRequest) {
  // Rate limiting
  const identifier = req.user?.id || req.ip || 'anonymous';
  if (!rateLimit(identifier, 50, 60000)) {
    return NextResponse.json(
      { error: 'Too many requests' },
      { status: 429 }
    );
  }

  return NextResponse.json({
    message: 'Access granted to protected resource',
    user: req.user,
    timestamp: new Date().toISOString(),
  });
}

// Example admin-only route
async function handleAdmin(req: AuthenticatedRequest) {
  return NextResponse.json({
    message: 'Admin access granted',
    user: req.user,
    adminData: 'sensitive information',
  });
}

export const GET = withApiAuth(handleProtected);

// Admin-only endpoint with role requirements
export const POST = withApiAuth(handleAdmin, {
  requiredRoles: ['admin', 'super_admin']
});