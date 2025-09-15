# API Documentation

This document provides comprehensive API documentation for the Kyros Praxis platform, including all service endpoints, authentication methods, request/response schemas, and usage examples.

## 📚 API Overview

The Kyros Praxis platform exposes multiple APIs for different services:

- **Orchestrator API** (`/api/v1`) - Core business logic and job orchestration
- **Console API** - Frontend application routes and NextAuth endpoints
- **Terminal Daemon API** - WebSocket terminal operations
- **Service Registry API** - Service discovery and health monitoring

## 🔐 Authentication & Authorization

### JWT Authentication

All protected API endpoints require JWT authentication. Tokens are obtained through the login endpoint:

```bash
# Login to get access token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_email&password=your_password"
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Using Access Tokens

Include the JWT token in the Authorization header for protected endpoints:

```bash
curl -X GET http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer your_access_token"
```

### Token Expiration

- Access tokens expire after 30 minutes
- Refresh tokens are not implemented in current version
- Users must re-authenticate after token expiration

## 🎯 Orchestrator API

### Base URL
- Development: `http://localhost:8000`
- Production: Configurable via environment variable

### Health Check Endpoints

#### GET `/healthz`
Health check with database connectivity verification.

**Response:**
```json
{
  "status": "ok"
}
```

**Status Codes:**
- `200` - Service healthy
- `500` - Database unavailable

#### GET `/health`
Basic health check without dependencies.

**Response:**
```json
{
  "status": "healthy"
}
```

### Authentication Endpoints

#### POST `/auth/login`
Authenticate user and receive JWT access token.

**Request Body:**
```json
{
  "username": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

**Status Codes:**
- `200` - Authentication successful
- `401` - Invalid credentials

### Jobs API (`/api/v1/jobs`)

#### POST `/api/v1/jobs`
Create a new job.

**Request Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "title": "New Job Title"
}
```

**Response:**
```json
{
  "id": "uuid-string",
  "name": "New Job Title",
  "status": "pending"
}
```

**Status Codes:**
- `201` - Job created successfully
- `400` - Invalid input
- `401` - Unauthorized
- `500` - Server error

#### GET `/api/v1/jobs`
List all jobs.

**Request Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "jobs": [
    {
      "id": "uuid-string",
      "name": "Job Name",
      "status": "pending"
    }
  ]
}
```

**Response Headers:**
- `ETag` - Entity tag for caching

#### GET `/api/v1/jobs/{job_id}`
Get specific job by ID.

**Request Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": "uuid-string",
  "name": "Job Name",
  "status": "pending"
}
```

**Status Codes:**
- `200` - Job found
- `404` - Job not found

#### DELETE `/api/v1/jobs/{job_id}`
Delete a job (not implemented).

**Status Codes:**
- `501` - Not implemented

### Tasks API (`/api/v1/collab`)

#### POST `/api/v1/collab/tasks`
Create a new task.

**Request Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "title": "Task Title",
  "description": "Task description",
  "version": 1
}
```

**Response:**
```json
{
  "id": "uuid-string",
  "title": "Task Title",
  "description": "Task description",
  "version": 1,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Response Headers:**
- `ETag` - Entity tag for caching
- `Location` - URL to the created task

**Status Codes:**
- `201` - Task created
- `400` - Invalid input
- `401` - Unauthorized

#### GET `/api/v1/collab/state/tasks`
List all tasks.

**Request Headers:**
- `Authorization: Bearer <token>` (required)

**Response:**
```json
{
  "kind": "tasks",
  "items": [
    {
      "id": "uuid-string",
      "title": "Task Title",
      "description": "Task description",
      "version": 1,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Response Headers:**
- `ETag` - Entity tag for caching

**Status Codes:**
- `200` - Tasks retrieved successfully
- `401` - Unauthorized

### Security API (`/api/v1/security`)

#### GET `/api/v1/security/health`
Security-focused health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "security": {
    "csp_enabled": true,
    "csrf_enabled": true,
    "rate_limiting": true,
    "jwt_enabled": true
  }
}
```

#### POST `/api/v1/security/csp-report`
Receive and log Content Security Policy violation reports.

**Request Body:**
```json
{
  "csp_report": {
    "document_uri": "https://example.com/page",
    "violated_directive": "script-src",
    "effective_directive": "script-src",
    "original_policy": "script-src 'self'",
    "blocked_uri": "https://evil.com/malicious.js",
    "status_code": 200
  }
}
```

**Response:**
```json
{
  "status": "reported"
}
```

#### GET `/api/v1/security/config`
Get current security configuration (redacted for security).

**Response:**
```json
{
  "environment": "production",
  "features": {
    "jwt_authentication": true,
    "csrf_protection": true,
    "rate_limiting": true,
    "csp_headers": true,
    "security_headers": true,
    "cors_policy": true
  },
  "jwt": {
    "algorithm": "HS512",
    "expiration_hours": 2
  }
}
```

### Monitoring API (`/api/v1/monitoring`)

#### GET `/api/v1/monitoring/health`
Comprehensive health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "service": "kyros-praxis",
  "version": "0.1.0",
  "environment": "production",
  "database": "healthy",
  "memory": "healthy"
}
```

#### GET `/api/v1/monitoring/metrics`
System metrics endpoint.

**Response:**
```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "system": {
    "cpu_usage": 45.2,
    "memory": {
      "total": 8589934592,
      "available": 4294967296,
      "used": 4294967296,
      "percentage": 50.0
    },
    "disk": {
      "total": 100000000000,
      "used": 50000000000,
      "free": 50000000000,
      "percentage": 50.0
    },
    "process": {
      "pid": 1234,
      "cpu_percent": 5.2,
      "memory_info": {...},
      "num_threads": 8,
      "create_time": "2024-01-01T00:00:00Z"
    }
  },
  "application": {
    "service": "kyros-praxis",
    "version": "0.1.0",
    "environment": "production",
    "python_version": "3.11.0"
  }
}
```

#### GET `/api/v1/monitoring/database/health`
Database health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "latency_ms": 5.2,
  "database_info": {
    "version": "PostgreSQL 15.0"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET `/api/v1/monitoring/logs/recent`
Get recent application logs (placeholder implementation).

**Response:**
```json
{
  "message": "Log retrieval not implemented",
  "note": "Use proper log aggregation system (ELK, Loki, etc.) for production",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET `/api/v1/monitoring/performance`
Application performance metrics (placeholder implementation).

**Response:**
```json
{
  "response_times": {
    "average_ms": 0,
    "95th_percentile_ms": 0,
    "99th_percentile_ms": 0
  },
  "throughput": {
    "requests_per_second": 0,
    "total_requests": 0
  },
  "error_rate": {
    "percentage": 0,
    "total_errors": 0
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "note": "Implement proper APM/metrics collection for production use"
}
```

#### GET `/api/v1/monitoring/dependencies`
Check external dependencies health.

**Response:**
```json
{
  "dependencies": {
    "redis": {"status": "not_configured"},
    "qdrant": {"status": "not_configured"}
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Utilities API (`/api/v1/utils`)

Various utility endpoints for internal operations.

### WebSocket Endpoint

#### WS `/ws`
WebSocket endpoint for real-time communication with authentication.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws', [
  'Authorization', 'Bearer your_token'
]);
```

**Message Format:**
```json
{
  "type": "message_type",
  "data": { /* message payload */ }
}
```

## 🖥️ Console API

### Base URL
- Development: `http://localhost:3001`
- Production: Configurable via environment variable

### Authentication Endpoints

#### GET/POST `/api/auth/[...nextauth]`
NextAuth authentication endpoints.

**Supported Providers:**
- Credentials (email/password)
- OAuth providers (configurable)

### Health Check

#### GET `/api/health`
Application health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 🔄 Terminal Daemon API

### WebSocket Endpoint
- Development: `ws://localhost:8787`
- Production: Configurable via `KYROS_DAEMON_PORT`

### WebSocket Protocol

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8787');
```

**Message Types:**

#### Terminal Command
```json
{
  "type": "command",
  "command": "ls -la",
  "id": "command-id"
}
```

#### Terminal Output
```json
{
  "type": "output",
  "data": "terminal output",
  "id": "command-id"
}
```

#### Session Management
```json
{
  "type": "session",
  "action": "create|destroy|resize",
  "id": "session-id"
}
```

### HTTP Endpoints

#### GET `/health`
Terminal daemon health check.

**Response:**
```json
{
  "status": "running",
  "sessions": 0,
  "uptime": 3600
}
```

## 📊 Data Models

### Job Model
```typescript
interface Job {
  id: string;           // UUID
  name: string;         // Job name/title
  status: string;       // pending, running, completed, failed
  created_at: string;   // ISO 8601 timestamp
}
```

### Task Model
```typescript
interface Task {
  id: string;           // UUID
  title: string;        // Task title
  description?: string; // Optional description
  version: number;      // Task version
  created_at: string;   // ISO 8601 timestamp
}
```

### User Model
```typescript
interface User {
  id: string;           // UUID
  email: string;        // User email (unique)
  password_hash: string; // Hashed password
}
```

### Event Model
```typescript
interface Event {
  id: string;           // UUID
  type: string;         // Event type
  payload: any;         // Event payload (JSON)
  created_at: string;   // ISO 8601 timestamp
}
```

## 🚨 Error Handling

### Structured Error Response Format
All API errors now return structured responses for better error handling:

```json
{
  "error": {
    "type": "http_exception",
    "code": 401,
    "message": "Could not validate credentials",
    "path": "/api/v1/collab/tasks",
    "method": "POST"
  }
}
```

### Legacy Error Response Format (Deprecated)
Some endpoints may still return the legacy format:

```json
{
  "detail": "Error message describing the issue"
}
```

### Common HTTP Status Codes

#### Success Codes
- `200 OK` - Request successful
- `201 Created` - Resource created
- `204 No Content` - Request successful, no response body

#### Client Error Codes
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required or failed
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error

#### Server Error Codes
- `500 Internal Server Error` - Server-side error
- `501 Not Implemented` - Endpoint not implemented
- `503 Service Unavailable` - Service temporarily unavailable

## 🔄 Rate Limiting

### JWT-Aware Rate Limiting
Rate limiting is now JWT-aware, using authenticated user IDs for fair usage:

- **Authenticated users**: Limited by user ID (prevents abuse per user)
- **Anonymous requests**: Limited by IP address
- **Login endpoint**: Stricter 5 requests/minute limit (prevents brute force)

### Default Limits
- **General API endpoints**: 100 requests per 15 minutes per user/IP
- **Login endpoint**: 5 requests per minute per IP
- **Rate limiting backend**: Redis (with in-memory fallback)

### Rate Limit Headers
When rate limits are enforced, the following headers are included:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
Retry-After: 60
```

## 🏷️ ETag Support

ETags are supported for cacheable endpoints to enable conditional requests:

### Making Conditional Requests
```bash
curl -X GET http://localhost:8000/api/v1/jobs \
  -H "If-None-Match: \"etag-value\""
```

**Responses:**
- `200 OK` - Resource modified, includes new ETag
- `304 Not Modified` - Resource not modified

## 🛡️ Security Headers

All API responses include security headers:

```
Content-Security-Policy: default-src 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

## 📝 API Testing

### Using curl

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=password" | \
  jq -r '.access_token')

# Create job
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Job"}'

# List jobs
curl -X GET http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer $TOKEN"
```

### Using Python

```python
import requests

# Login
login_url = "http://localhost:8000/auth/login"
response = requests.post(login_url, data={
    "username": "test@example.com",
    "password": "password"
})
token = response.json()["access_token"]

# Set up headers
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Create job
job_response = requests.post(
    "http://localhost:8000/api/v1/jobs",
    headers=headers,
    json={"title": "Test Job"}
)
print(job_response.json())
```

### Using JavaScript/Node.js

```javascript
// Login
const loginResponse = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: new URLSearchParams({
    username: 'test@example.com',
    password: 'password'
  })
});

const { access_token } = await loginResponse.json();

// Create job
const jobResponse = await fetch('http://localhost:8000/api/v1/jobs', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ title: 'Test Job' })
});

const job = await jobResponse.json();
console.log(job);
```

## 🔧 OpenAPI Specification

The Orchestrator API exposes an OpenAPI specification at:

```
GET /api/v1/openapi.json
```

You can use this with tools like:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 📚 SDK Libraries

### Python SDK
```python
# Installation
pip install kyros-praxis-sdk

# Usage
from kyros_praxis import OrchestratorClient

client = OrchestratorClient(
    base_url="http://localhost:8000",
    username="test@example.com",
    password="password"
)

# Create job
job = client.jobs.create(title="Test Job")
print(job)
```

### TypeScript/JavaScript SDK
```typescript
// Installation
npm install @kyros-praxis/sdk

// Usage
import { OrchestratorClient } from '@kyros-praxis/sdk';

const client = new OrchestratorClient({
  baseUrl: 'http://localhost:8000',
  username: 'test@example.com',
  password: 'password'
});

// Create job
const job = await client.jobs.create({ title: 'Test Job' });
console.log(job);
```

## 🔗 Additional Resources

- [Architecture Overview](../architecture/overview.md)
- [Security Guidelines](../security/README.md)
- [Development Setup](../../README.md)
- [OpenAPI Specification](../specs/openapi.yaml)