import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/auth-v5';
import { jwtDecode } from 'jwt-decode';

export interface AuthenticatedRequest extends NextRequest {
  user?: {
    id: string;
    email: string;
    name: string;
    roles?: string[];
  };
}

// Middleware for API route protection
export function withApiAuth(
  handler: (req: AuthenticatedRequest) => Promise<NextResponse> | NextResponse,
  options: { 
    requiredRoles?: string[];
    allowAnonymous?: boolean;
  } = {}
) {
  return async (req: NextRequest): Promise<NextResponse> => {
    try {
      // Get token from Authorization header or NextAuth session
      let token = req.headers.get('authorization')?.replace('Bearer ', '');
      
      if (!token) {
        // Try to get session from NextAuth
        const session = await auth();
        token = (session as any)?.accessToken;
      }

      if (!token && !options.allowAnonymous) {
        return NextResponse.json(
          { error: 'Authentication required' },
          { status: 401 }
        );
      }

      let user = null;
      if (token) {
        try {
          const decoded: any = jwtDecode(token);
          
          // Check if token is expired
          const currentTime = Date.now() / 1000;
          if (decoded.exp < currentTime) {
            return NextResponse.json(
              { error: 'Token expired' },
              { status: 401 }
            );
          }

          user = {
            id: decoded.sub || decoded.id,
            email: decoded.email,
            name: decoded.name,
            roles: decoded.roles || [],
          };
        } catch (error) {
          return NextResponse.json(
            { error: 'Invalid token' },
            { status: 401 }
          );
        }
      }

      // Check role requirements
      if (options.requiredRoles && user) {
        const hasRequiredRole = options.requiredRoles.some(role => 
          user.roles?.includes(role)
        );
        
        if (!hasRequiredRole) {
          return NextResponse.json(
            { error: 'Insufficient permissions' },
            { status: 403 }
          );
        }
      }

      // Add user to request
      const authenticatedReq = req as AuthenticatedRequest;
      if (user) {
        authenticatedReq.user = user;
      }

      return await handler(authenticatedReq);
    } catch (error) {
      console.error('API auth middleware error:', error);
      return NextResponse.json(
        { error: 'Internal server error' },
        { status: 500 }
      );
    }
  };
}

// Utility function to validate session on the server side
export async function validateSession(req: NextRequest) {
  try {
    const session = await auth();
    return session;
  } catch (error) {
    console.error('Session validation error:', error);
    return null;
  }
}

// Rate limiting helper (simple in-memory implementation)
const rateLimitMap = new Map<string, { count: number; resetTime: number }>();

export function rateLimit(
  identifier: string,
  limit: number = 100,
  windowMs: number = 60000 // 1 minute
): boolean {
  const now = Date.now();
  const windowStart = now - windowMs;
  
  const record = rateLimitMap.get(identifier);
  
  if (!record || record.resetTime < windowStart) {
    rateLimitMap.set(identifier, { count: 1, resetTime: now + windowMs });
    return true;
  }
  
  if (record.count >= limit) {
    return false;
  }
  
  record.count++;
  return true;
}

// Cleanup expired rate limit entries periodically
setInterval(() => {
  const now = Date.now();
  for (const [key, record] of rateLimitMap.entries()) {
    if (record.resetTime < now) {
      rateLimitMap.delete(key);
    }
  }
}, 60000); // Clean up every minute