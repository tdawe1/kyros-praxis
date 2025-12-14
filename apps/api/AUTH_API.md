# Authentication API Documentation

## Overview

The Kyros Praxis CrewAI API now supports JWT-based authentication for user registration and login. Authentication is **optional** for most endpoints but can be used to track which user created each crew run.

**Base URL**: `http://localhost:8001`

---

## Quick Start

### 1. Install Dependencies

```bash
cd api
pip install -r requirements.txt
```

### 2. Set JWT Secret Key

Generate a secure secret key:
```bash
openssl rand -hex 32
```

Add to your `.env` file:
```bash
JWT_SECRET_KEY=your-generated-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
```

### 3. Run Database Migration

```bash
# Apply the users table migration
alembic upgrade head
```

### 4. Start the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

---

## Endpoints

### POST `/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "email": "john@example.com",
  "role": "user",
  "active": true,
  "created_at": "2025-01-12T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Username or email already exists
- `422 Unprocessable Entity` - Invalid input (e.g., password too short)

---

### POST `/auth/login`

Authenticate and receive JWT access token.

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
- `401 Unauthorized` - Incorrect email or password
- `422 Unprocessable Entity` - Invalid input format

---

### GET `/auth/me`

Get current authenticated user information.

**Headers:**
```
Authorization: Bearer <your_access_token>
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "email": "john@example.com",
  "role": "user",
  "active": true,
  "created_at": "2025-01-12T10:30:00Z"
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token

---

## Frontend Integration

### React Example with Fetch

```typescript
// Register new user
async function register(username: string, email: string, password: string) {
  const response = await fetch('http://localhost:8001/auth/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, email, password }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
}

// Login
async function login(email: string, password: string) {
  const response = await fetch('http://localhost:8001/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
  
  if (!response.ok) {
    throw new Error('Invalid credentials');
  }
  
  const data = await response.json();
  // Store token in localStorage or state management
  localStorage.setItem('access_token', data.access_token);
  return data;
}

// Get current user
async function getCurrentUser() {
  const token = localStorage.getItem('access_token');
  if (!token) {
    throw new Error('Not authenticated');
  }
  
  const response = await fetch('http://localhost:8001/auth/me', {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  
  if (!response.ok) {
    throw new Error('Failed to get user info');
  }
  
  return await response.json();
}

// Create crew run with authentication
async function createRun(crewId: string, input: any) {
  const token = localStorage.getItem('access_token');
  const headers: any = {
    'Content-Type': 'application/json',
  };
  
  // Add auth header if token exists (optional)
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch('http://localhost:8001/crews/runs', {
    method: 'POST',
    headers,
    body: JSON.stringify({
      crew_id: crewId,
      input,
    }),
  });
  
  return await response.json();
}
```

---

### React Context Example

```typescript
// AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  active: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (username: string, email: string, password: string) => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(
    localStorage.getItem('access_token')
  );

  useEffect(() => {
    if (token) {
      fetchCurrentUser();
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      const response = await fetch('http://localhost:8001/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        logout();
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    }
  };

  const login = async (email: string, password: string) => {
    const response = await fetch('http://localhost:8001/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const data = await response.json();
    setToken(data.access_token);
    localStorage.setItem('access_token', data.access_token);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('access_token');
  };

  const register = async (username: string, email: string, password: string) => {
    const response = await fetch('http://localhost:8001/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }

    // Auto-login after registration
    await login(email, password);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        logout,
        register,
        isAuthenticated: !!token && !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
```

---

## Token Management

### Token Expiration

- Default expiration: **24 hours** (1440 minutes)
- Configurable via `JWT_EXPIRE_MINUTES` env variable
- No refresh token mechanism yet (coming in future update)

### Token Storage

**Recommended approaches:**

1. **localStorage** (simple, works for most cases):
   ```typescript
   localStorage.setItem('access_token', token);
   ```

2. **sessionStorage** (more secure, cleared on tab close):
   ```typescript
   sessionStorage.setItem('access_token', token);
   ```

3. **HTTP-only cookies** (most secure, requires backend changes):
   - Not currently supported
   - Planned for future update

### Token Validation

The API automatically validates tokens on protected endpoints. If a token is expired or invalid, you'll receive a `401 Unauthorized` response.

**Handle expired tokens:**
```typescript
async function makeAuthenticatedRequest(url: string, options: RequestInit = {}) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
    },
  });
  
  if (response.status === 401) {
    // Token expired or invalid - redirect to login
    localStorage.removeItem('access_token');
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  
  return response;
}
```

---

## Security Best Practices

### For Development

1. **Use a strong JWT secret**:
   ```bash
   # Generate with:
   openssl rand -hex 32
   ```

2. **Never commit `.env` files** to version control

3. **Use HTTPS in production** (tokens sent in headers are vulnerable over HTTP)

### For Frontend

1. **Validate input before sending** to API
2. **Handle token expiration gracefully**
3. **Clear tokens on logout**
4. **Don't log tokens** in console or error messages

---

## Optional Authentication

Authentication is **optional** for crew run endpoints. You can:

- **Create runs without auth**: Just omit the `Authorization` header
- **Create runs with auth**: Include `Authorization: Bearer <token>` to track ownership

Example:
```typescript
// Without auth (anonymous)
fetch('http://localhost:8001/crews/runs', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ crew_id: 'spec_to_tasks', input: { prompt: 'Hello' } }),
});

// With auth (tracked to user)
fetch('http://localhost:8001/crews/runs', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer eyJhbGciOi...',
  },
  body: JSON.stringify({ crew_id: 'spec_to_tasks', input: { prompt: 'Hello' } }),
});
```

---

## Testing with cURL

### Register
```bash
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}'
```

### Login
```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

### Get Current User
```bash
TOKEN="your-token-here"
curl -X GET http://localhost:8001/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## Troubleshooting

### "JWT_SECRET_KEY must be set"

**Problem**: API won't start without a JWT secret.

**Solution**: Add to `.env`:
```bash
JWT_SECRET_KEY=$(openssl rand -hex 32)
```

### "Could not validate credentials"

**Problem**: Token is expired or invalid.

**Solution**:
- Check token hasn't expired (24 hours default)
- Verify token format: `Bearer <token>`
- Try logging in again to get fresh token

### "Username already registered"

**Problem**: Username or email already exists.

**Solution**:
- Use a different username/email
- Or login with existing credentials

---

## API Documentation (Swagger)

Interactive API docs available at:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

Test authentication endpoints directly in the browser!

---

## Future Enhancements

Planned for upcoming releases:

- [ ] Refresh token mechanism
- [ ] Password reset flow
- [ ] Email verification
- [ ] Role-based access control (RBAC) enforcement
- [ ] OAuth2 integration (Google, GitHub)
- [ ] Rate limiting per user
- [ ] Admin endpoints for user management

---

## Support

For issues or questions:
1. Check the [main README](README.md)
2. Review [apps/README.md](../README.md) for architecture overview
3. See [CREWAI-MIGRATION-STATUS.md](../../CREWAI-MIGRATION-STATUS.md) for project status
