# Frontend Integration Guide - Security Updates

**Date**: October 12, 2025  
**Status**: Required frontend changes for backend security updates

---

## Overview

The backend has been updated with JWT authentication for WebSocket terminals, correlation IDs, and enhanced security. The frontend needs corresponding updates to integrate with these changes.

---

## Required Changes

### 1. WebSocket Authentication (CRITICAL)

**Issue**: Terminal WebSocket now requires JWT authentication  
**Priority**: HIGH - Terminal won't work without this

**Current Code** (`Terminal.tsx`):
```typescript
const ws = new WebSocket(TERMINAL_WS_URL);
// No authentication!
```

**Required Changes**:

#### Option A: Token in Query Parameter (Simpler)
```typescript
import { ACCESS_TOKEN_STORAGE_KEY, withTokenQuery } from '@/app/lib/api';

// Get token from storage
const token = localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
if (!token) {
  term.writeln('Error: Not authenticated');
  return;
}

// Add token to URL
const wsUrl = withTokenQuery(TERMINAL_WS_URL, token);
const ws = new WebSocket(wsUrl);
```

#### Option B: Token in First Message (More Secure)
```typescript
const ws = new WebSocket(TERMINAL_WS_URL);

ws.onopen = () => {
  // Send auth message first
  const token = localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
  if (token) {
    ws.send(JSON.stringify({
      type: 'auth',
      token: token
    }));
  }
};

ws.onmessage = (event) => {
  // Handle auth response
  if (typeof event.data === 'string') {
    try {
      const msg = JSON.parse(event.data);
      
      if (msg.type === 'auth_success') {
        term.writeln(`Authenticated as ${msg.user.username}`);
        flushPending(); // Send buffered commands
        return;
      }
      
      if (msg.type === 'error') {
        term.writeln(`\r\nError: ${msg.message}`);
        ws.close();
        return;
      }
    } catch {
      // Not JSON, treat as terminal output
      term.write(event.data);
    }
  }
  // ... handle binary data
};
```

---

### 2. Correlation ID Support (RECOMMENDED)

**Issue**: Backend sends X-Correlation-ID for request tracing  
**Priority**: MEDIUM - Improves debugging

**Changes to `api.ts`**:

```typescript
// Add correlation ID storage
let currentCorrelationId: string | null = null;

export const getCorrelationId = () => currentCorrelationId;

// Update fetch wrapper to include correlation IDs
export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  // Add correlation ID if we have one
  if (currentCorrelationId) {
    headers['X-Correlation-ID'] = currentCorrelationId;
  }
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });
  
  // Save correlation ID from response
  const correlationId = response.headers.get('X-Correlation-ID');
  if (correlationId) {
    currentCorrelationId = correlationId;
  }
  
  if (!response.ok) {
    // Include correlation ID in errors for debugging
    const error = await response.json().catch(() => ({}));
    throw new Error(
      `API Error: ${response.statusText} (Correlation ID: ${correlationId || 'none'})`
    );
  }
  
  return response.json();
}
```

---

### 3. Enhanced Error Handling (REQUIRED)

**Issue**: New error response format from backend  
**Priority**: HIGH - Improves UX

**Error Response Format**:
```json
{
  "error": "Validation Error",
  "message": "The request data failed validation",
  "details": [
    {
      "field": "email",
      "message": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

**Error Handler**:
```typescript
export class APIError extends Error {
  constructor(
    public status: number,
    public error: string,
    public details?: any,
    public correlationId?: string
  ) {
    super(error);
    this.name = 'APIError';
  }
}

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  // ... headers setup ...
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });
  
  const correlationId = response.headers.get('X-Correlation-ID');
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new APIError(
      response.status,
      errorData.message || response.statusText,
      errorData.details,
      correlationId || undefined
    );
  }
  
  return response.json();
}
```

---

### 4. Auth Context Updates (RECOMMENDED)

**Issue**: Terminal needs auth state  
**Priority**: MEDIUM - Better UX

**Update `auth-context.tsx`**:

```typescript
interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  // NEW: Check if token is still valid
  isTokenValid: () => boolean;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // ... existing code ...
  
  const isTokenValid = useCallback(() => {
    if (!token) return false;
    
    try {
      // Decode JWT to check expiration
      const payload = JSON.parse(atob(token.split('.')[1]));
      const exp = payload.exp * 1000; // Convert to milliseconds
      return Date.now() < exp;
    } catch {
      return false;
    }
  }, [token]);
  
  // Auto-refresh or logout on token expiration
  useEffect(() => {
    if (token && !isTokenValid()) {
      console.warn('Token expired, logging out');
      logout();
    }
  }, [token, isTokenValid, logout]);
  
  return (
    <AuthContext.Provider 
      value={{ user, token, login, logout, isAuthenticated, isTokenValid }}
    >
      {children}
    </AuthContext.Provider>
  );
}
```

---

## Implementation Files

### File 1: Updated `Terminal.tsx`

**Location**: `apps/console/app/terminal/components/Terminal.tsx`

**Changes**:
1. Add authentication before connecting
2. Handle JSON messages (auth_success, error)
3. Buffer commands until authenticated
4. Show auth status to user

### File 2: Updated `api.ts`

**Location**: `apps/console/app/lib/api.ts`

**Changes**:
1. Add correlation ID support
2. Create `apiFetch` wrapper with proper error handling
3. Add `APIError` class
4. Export correlation ID getter

### File 3: Updated `auth-context.tsx`

**Location**: `apps/console/app/state/auth-context.tsx`

**Changes**:
1. Add `isTokenValid()` method
2. Add auto-logout on expiration
3. Export token for WebSocket use

---

## Step-by-Step Implementation

### Step 1: Update API Client (Required)

Create `apps/console/app/lib/api-client.ts`:

```typescript
import { ACCESS_TOKEN_STORAGE_KEY, API_BASE } from './api';

let currentCorrelationId: string | null = null;

export class APIError extends Error {
  constructor(
    public status: number,
    public error: string,
    public details?: any,
    public correlationId?: string
  ) {
    super(error);
    this.name = 'APIError';
  }
}

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  if (currentCorrelationId) {
    headers['X-Correlation-ID'] = currentCorrelationId;
  }
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });
  
  const correlationId = response.headers.get('X-Correlation-ID');
  if (correlationId) {
    currentCorrelationId = correlationId;
  }
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new APIError(
      response.status,
      errorData.message || response.statusText,
      errorData.details,
      correlationId || undefined
    );
  }
  
  return response.json();
}

export const getCorrelationId = () => currentCorrelationId;
```

### Step 2: Update Terminal Component (Critical)

**Add to `Terminal.tsx` before WebSocket creation**:

```typescript
// At the top of useEffect
const token = localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
if (!token) {
  term.writeln('Error: Not authenticated. Please log in.');
  return;
}

// Use token in WebSocket URL
const wsUrl = withTokenQuery(TERMINAL_WS_URL, token);
const ws = new WebSocket(wsUrl);
ws.binaryType = 'arraybuffer';
wsRef.current = ws;

// Track auth state
let isAuthenticated = false;

term.writeln('Connecting to terminal...');

ws.onopen = () => {
  // If using query param auth, we're authenticated immediately
  isAuthenticated = true;
  flushPending();
  term.writeln('\r\nConnected. Type commands to get started.\r\n');
};

ws.onmessage = (event) => {
  // Handle JSON messages (auth responses)
  if (typeof event.data === 'string') {
    try {
      const msg = JSON.parse(event.data);
      
      if (msg.type === 'auth_success') {
        isAuthenticated = true;
        term.writeln(`\r\nAuthenticated as ${msg.user.username}\r\n`);
        flushPending();
        return;
      }
      
      if (msg.type === 'error') {
        term.writeln(`\r\nError: ${msg.message}\r\n`);
        return;
      }
      
      // Not a recognized JSON message, treat as text
      term.write(event.data);
    } catch {
      // Not JSON, treat as terminal output
      term.write(event.data);
    }
    return;
  }
  
  // Handle binary data (terminal output)
  if (event.data instanceof ArrayBuffer) {
    term.write(textDecoder.decode(event.data));
    return;
  }
  
  if (event.data instanceof Blob) {
    event.data
      .arrayBuffer()
      .then((buffer) => term.write(textDecoder.decode(buffer)))
      .catch((error) => {
        console.error('Failed to decode terminal Blob payload', error);
      });
  }
};

ws.onerror = (error) => {
  console.error('Terminal WebSocket error', error);
  term.writeln('\r\n[Connection error - please check authentication]');
};

ws.onclose = (event) => {
  if (event.code === 1008) {
    term.writeln('\r\n[Connection closed: Authentication failed]');
  } else {
    term.writeln('\r\n[Connection closed]');
  }
};
```

### Step 3: Update Auth Context (Recommended)

**Add to `auth-context.tsx`**:

```typescript
const isTokenValid = useCallback(() => {
  if (!token) return false;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000;
    return Date.now() < exp;
  } catch {
    return false;
  }
}, [token]);

// Auto-logout on expiration
useEffect(() => {
  if (token && !isTokenValid()) {
    logout();
  }
}, [token, isTokenValid, logout]);
```

---

## Testing

### Test 1: Terminal Authentication

```bash
# 1. Start backend
cd apps/api
../../.venv/bin/uvicorn app.main:app --reload

# 2. Start frontend
cd apps/console
npm run dev

# 3. Test flow:
# - Open http://localhost:3000
# - Login with user account
# - Navigate to /terminal
# - Terminal should connect and show username
# - Try typing commands
```

**Expected Behavior**:
- Without login: "Error: Not authenticated"
- With login: "Authenticated as {username}"
- Commands work immediately

### Test 2: Correlation IDs

```bash
# Open browser DevTools Network tab
# Make any API request
# Check Response Headers for X-Correlation-ID
# Check subsequent Request Headers include same ID
```

### Test 3: Error Handling

```bash
# Try invalid API call
# Should show proper error with correlation ID
```

---

## Migration Checklist

- [ ] Create `api-client.ts` with apiFetch wrapper
- [ ] Update `Terminal.tsx` to use authenticated WebSocket
- [ ] Update `auth-context.tsx` with token validation
- [ ] Test terminal with authentication
- [ ] Test terminal without authentication (should show error)
- [ ] Verify correlation IDs in Network tab
- [ ] Test error handling with invalid requests
- [ ] Update other components using fetch() to use apiFetch()
- [ ] Add loading states for terminal connection
- [ ] Add reconnection logic for WebSocket

---

## Optional Enhancements

### 1. WebSocket Reconnection

```typescript
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

function connectWebSocket() {
  const token = localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
  if (!token) {
    term.writeln('Error: Not authenticated');
    return;
  }
  
  const wsUrl = withTokenQuery(TERMINAL_WS_URL, token);
  const ws = new WebSocket(wsUrl);
  
  ws.onclose = (event) => {
    if (event.code === 1008) {
      term.writeln('\r\n[Authentication failed]');
      return;
    }
    
    if (reconnectAttempts < maxReconnectAttempts) {
      reconnectAttempts++;
      term.writeln(`\r\n[Reconnecting... (${reconnectAttempts}/${maxReconnectAttempts})]`);
      setTimeout(connectWebSocket, 2000 * reconnectAttempts);
    } else {
      term.writeln('\r\n[Connection lost. Refresh to reconnect.]');
    }
  };
  
  ws.onopen = () => {
    reconnectAttempts = 0;
    // ... rest of logic
  };
}
```

### 2. Connection Status Indicator

```typescript
// Add to Terminal.tsx
const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');

// In component JSX:
<div className="flex items-center gap-2">
  <div className={`h-2 w-2 rounded-full ${
    connectionStatus === 'connected' ? 'bg-green-500' :
    connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
    'bg-red-500'
  }`} />
  <span className="text-sm text-gray-400">
    {connectionStatus === 'connected' ? 'Connected' :
     connectionStatus === 'connecting' ? 'Connecting...' :
     'Disconnected'}
  </span>
</div>
```

### 3. Token Refresh Before Terminal Connection

```typescript
async function refreshTokenIfNeeded() {
  const token = localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
  if (!token) return false;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000;
    const timeUntilExpiry = exp - Date.now();
    
    // Refresh if token expires in < 5 minutes
    if (timeUntilExpiry < 5 * 60 * 1000) {
      // Call refresh endpoint
      const newToken = await apiFetch<{token: string}>('/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: token })
      });
      localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, newToken.token);
    }
    
    return true;
  } catch {
    return false;
  }
}
```

---

## Summary

**Critical Changes** (Terminal won't work without these):
1. ✅ Add JWT token to WebSocket connection
2. ✅ Handle auth_success and error messages
3. ✅ Buffer commands until authenticated

**Recommended Changes** (Better UX):
1. ✅ Add correlation ID support
2. ✅ Enhance error handling
3. ✅ Add token validation

**Optional Enhancements** (Nice to have):
1. WebSocket reconnection
2. Connection status indicator
3. Token refresh before connection

**Estimated Time**: 2-3 hours for critical changes, 4-5 hours for all recommended changes

---

**Last Updated**: October 12, 2025  
**Status**: Implementation Guide Ready
