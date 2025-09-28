# JWT/OAuth2 Authentication Setup

This document describes the authentication system implemented for the Kyros Console service using NextAuth.js v5.

## Features

### ✅ Implemented
- **OAuth2 Providers**: Google and GitHub OAuth2 login
- **JWT Token Handling**: Secure token generation, validation, and refresh
- **Secure Cookie Storage**: HttpOnly cookies with proper security flags
- **Session Management**: Login state persists across page refreshes
- **Proper Logout**: Token invalidation and cleanup
- **Route Protection**: Middleware-based authentication for protected routes
- **Fallback Authentication**: Credentials-based login for development

### 🔧 Authentication Providers

#### Google OAuth2
- Requires `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
- Redirects to Google for authentication
- Stores OAuth access token for API access

#### GitHub OAuth2
- Requires `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`
- Redirects to GitHub for authentication
- Stores OAuth access token for API access

#### Credentials (Dev/Fallback)
- Email/password authentication
- Integrates with orchestrator API
- Dev bypass option available

## Setup Instructions

### 1. Environment Configuration

Copy the example environment file and configure your OAuth credentials:

```bash
cp .env.example .env.local
```

Required environment variables:

```env
# NextAuth Configuration
NEXTAUTH_SECRET=your-secret-key-here
NEXTAUTH_URL=http://localhost:3000

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# GitHub OAuth
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_AUTH_URL=http://localhost:8000
NEXT_PUBLIC_ALLOW_DEV_LOGIN=true
NEXT_PUBLIC_POST_LOGIN_ROUTE=/agents
```

### 2. OAuth Provider Setup

#### Google OAuth2 Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Set authorized redirect URIs:
   - Development: `http://localhost:3000/api/auth/callback/google`
   - Production: `https://yourdomain.com/api/auth/callback/google`

#### GitHub OAuth2 Setup
1. Go to GitHub → Settings → Developer settings → OAuth Apps
2. Click "New OAuth App"
3. Set Authorization callback URL:
   - Development: `http://localhost:3000/api/auth/callback/github`
   - Production: `https://yourdomain.com/api/auth/callback/github`

### 3. Security Configuration

The authentication system includes several security features:

- **HttpOnly Cookies**: Prevents XSS attacks
- **Secure Flags**: HTTPS-only in production
- **CSRF Protection**: Built into NextAuth
- **Route Protection**: Middleware-based authentication
- **Token Expiration**: 30-day session lifetime

## Usage

### Login Component

The auth page (`/app/auth/page.tsx`) provides:
- OAuth2 login buttons for Google and GitHub
- Email/password form for credentials auth
- Proper error handling and loading states

### Logout Component

Use the `LogoutButton` component anywhere in your app:

```tsx
import LogoutButton from '@/app/components/LogoutButton';

export default function MyComponent() {
  return (
    <LogoutButton className="btn btn-secondary">
      Sign Out
    </LogoutButton>
  );
}
```

### Session Access

Access the current session in client components:

```tsx
import { useSession } from 'next-auth/react';

export default function MyComponent() {
  const { data: session, status } = useSession();
  
  if (status === 'loading') return <p>Loading...</p>;
  if (status === 'unauthenticated') return <p>Not signed in</p>;
  
  return <p>Signed in as {session.user.email}</p>;
}
```

Access session in server components:

```tsx
import { auth } from '@/lib/auth-v5';

export default async function ServerComponent() {
  const session = await auth();
  
  if (!session) return <p>Not signed in</p>;
  
  return <p>Signed in as {session.user.email}</p>;
}
```

## Testing

The authentication system includes comprehensive tests:

- **Auth Page Tests**: UI rendering and interaction
- **Logout Button Tests**: Component behavior
- **Integration Tests**: Authentication flows

Run tests with:

```bash
npm test
```

## Route Protection

The middleware automatically protects routes. Configure protected/public routes in `middleware.ts`:

```typescript
// Public routes that don't require authentication
const isPublicRoute = [
  '/auth',
  '/auth/login', 
  '/api/auth',
  '/health'
].some(path => nextUrl.pathname.startsWith(path))
```

## Troubleshooting

### Common Issues

1. **OAuth callback errors**: Check redirect URIs match exactly
2. **Session not persisting**: Verify `NEXTAUTH_SECRET` is set
3. **HTTPS required**: OAuth providers require HTTPS in production
4. **CORS issues**: Ensure API allows requests from frontend domain

### Development Mode

For development, you can bypass OAuth and use credentials:

```env
NEXT_PUBLIC_ALLOW_DEV_LOGIN=true
```

This enables the email/password form with dev credentials.