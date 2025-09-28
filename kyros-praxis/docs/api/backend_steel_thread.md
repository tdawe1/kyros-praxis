# Backend Steel Thread API Documentation

## Overview

This document describes the Backend Steel Thread API endpoints implemented in the orchestrator service. The API follows RESTful conventions with JWT authentication, ETag-based caching, and structured error responses.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All endpoints (except `/auth/login` and health checks) require JWT authentication. The token must be included in the `Authorization` header as a Bearer token:

```
Authorization: Bearer <your_jwt_token>
```

### Authentication Flow

1. **Login**: Send credentials to `/auth/login`
2. **Receive Token**: Get back a JWT access token
3. **Include Token**: Add the token to the `Authorization` header for subsequent requests
4. **Token Expiration**: Tokens expire after 30 minutes (configurable)

## Error Response Format

All error responses follow this structure:

```json
{
  "error": {
    "type": "http_exception|internal_server_error|validation_error",
    "code": 400|401|403|404|422|500,
    "message": "Human-readable error message",
    "path": "/api/v1/endpoint",
    "method": "GET|POST|PUT|DELETE"
  }
}
```

## ETag Usage

The API supports ETag-based conditional requests for efficient caching:

- **ETag Generation**: SHA-256 hash of the canonical JSON response
- **Response Headers**: `ETag` header included in GET responses
- **Conditional GET**: Include `If-None-Match` header to receive 304 Not Modified if unchanged
- **Idempotency**: ETags ensure responses are consistent for the same resource state

---

## Endpoints

### Health Checks

#### GET /health
Basic health check without database dependency.

**Response:**
```json
{
  "status": "healthy"
}
```

**Status Codes:**
- 200 OK - Service is healthy

#### GET /healthz
Health check with database connectivity verification.

**Response:**
```json
{
  "status": "ok"
}
```

**Status Codes:**
- 200 OK - Service and database are healthy
- 500 Internal Server Error - Database unavailable

---

### Authentication

#### POST /auth/login
Authenticate user and receive JWT access token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "jwt_token_string",
  "token_type": "bearer"
}
```

**Status Codes:**
- 200 OK - Authentication successful
- 401 Unauthorized - Invalid credentials
- 422 Unprocessable Entity - Invalid request format

---

### Jobs Management

#### POST /api/v1/jobs
Create a new job.

**Headers:**
- `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "title": "Job title (required, min 1 char)",
  "description": "Optional job description"
}
```

**Response:**
```json
{
  "id": "uuid-string",
  "name": "Job title",
  "status": "pending"
}
```

**Headers:**
- `ETag: "sha256-hash"`

**Status Codes:**
- 201 Created - Job created successfully
- 400 Bad Request - Invalid input
- 401 Unauthorized - Authentication required
- 422 Unprocessable Entity - Validation error
- 500 Internal Server Error - Creation failed

#### GET /api/v1/jobs
List all jobs.

**Headers:**
- `Authorization: Bearer <token>`
- `If-None-Match: <etag>` (optional)

**Response:**
```json
{
  "jobs": [
    {
      "id": "uuid-string",
      "name": "Job title",
      "status": "pending"
    }
  ]
}
```

**Headers:**
- `ETag: "sha256-hash"`

**Status Codes:**
- 200 OK - Success
- 304 Not Modified - Resource unchanged (if `If-None-Match` provided)
- 401 Unauthorized - Authentication required

#### GET /api/v1/jobs/{job_id}
Get a specific job by ID.

**Headers:**
- `Authorization: Bearer <token>`

**Path Parameters:**
- `job_id` - UUID of the job

**Response:**
```json
{
  "id": "uuid-string",
  "name": "Job title",
  "status": "pending"
}
```

**Headers:**
- `ETag: "sha256-hash"`

**Status Codes:**
- 200 OK - Success
- 401 Unauthorized - Authentication required
- 404 Not Found - Job not found

#### DELETE /api/v1/jobs/{job_id}
Delete a job.

**Headers:**
- `Authorization: Bearer <token>`

**Path Parameters:**
- `job_id` - UUID of the job

**Status Codes:**
- 501 Not Implemented - Endpoint not yet implemented

---

### Task Management (Collaboration)

#### POST /api/v1/collab/tasks
Create a new collaboration task.

**Headers:**
- `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "title": "Task title (required, min 1 char)",
  "description": "Optional task description"
}
```

**Response:**
```json
{
  "id": "uuid-string",
  "title": "Task title",
  "description": "Task description",
  "version": 1,
  "created_at": "2025-01-14T10:00:00.000000"
}
```

**Headers:**
- `ETag: "sha256-hash"`
- `Location: /api/v1/collab/tasks/{task_id}`

**Status Codes:**
- 201 Created - Task created successfully
- 400 Bad Request - Invalid input
- 401 Unauthorized - Authentication required
- 422 Unprocessable Entity - Validation error

#### GET /api/v1/collab/state/tasks
List all collaboration tasks.

**Headers:**
- `Authorization: Bearer <token>`
- `If-None-Match: <etag>` (optional)

**Response:**
```json
{
  "kind": "tasks",
  "items": [
    {
      "id": "uuid-string",
      "title": "Task title",
      "description": "Task description",
      "version": 1,
      "created_at": "2025-01-14T10:00:00.000000"
    }
  ]
}
```

**Headers:**
- `ETag: "sha256-hash"`

**Status Codes:**
- 200 OK - Success
- 304 Not Modified - Resource unchanged (if `If-None-Match` provided)
- 401 Unauthorized - Authentication required

---

### WebSocket

#### WS /ws
Authenticated WebSocket endpoint for real-time communication.

**Authentication:**
- Query parameter: `?token=<jwt_token>`
- OR Header: `Authorization: Bearer <token>`

**Connection Flow:**
1. Connect with authentication token
2. Server validates token and accepts connection
3. Server sends initial connection message
4. Client can send JSON messages
5. Server echoes messages with metadata

**Initial Connection Message:**
```json
{
  "type": "connection",
  "status": "connected",
  "user": "username",
  "timestamp": "2025-01-14T10:00:00.000000"
}
```

**Message Format:**
```json
{
  "type": "message",
  "data": { /* your message data */ },
  "timestamp": "2025-01-14T10:00:00.000000",
  "user": "username"
}
```

**Error Responses:**
- 1008 Policy Violation - Missing or invalid token
- 1011 Internal Error - Server error

---

## Data Models

### Job
```typescript
interface Job {
  id: string;        // UUID
  name: string;      // Title from JobCreate
  status: string;    // Current status
}
```

### Task
```typescript
interface Task {
  id: string;              // UUID
  title: string;           // Required, min 1 char
  description?: string;    // Optional
  version: number;         // Starts at 1
  created_at: string;      // ISO 8601 timestamp
}
```

### JobCreate/TaskCreate
```typescript
interface BaseCreate {
  title: string;           // Required, min 1 char, stripped whitespace
  description?: string;    // Optional
}
```

---

## Security Features

### JWT Claims
All JWT tokens include standard claims:
- `sub` - Subject (username)
- `iss` - Issuer
- `aud` - Audience
- `exp` - Expiration time
- `iat` - Issued at

### Rate Limiting
- Configured per endpoint
- Uses JWT user ID when available
- Falls back to IP address
- Prevents abuse and DoS attacks

### CORS
- Configured origins in settings
- Supports development and production environments

### Input Validation
- Pydantic models for request validation
- Type checking and constraints
- Detailed error messages

---

## Example Requests

### 1. Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secret"}'
```

### 2. Create Job
```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Process payroll", "description": "Monthly payroll processing"}'
```

### 3. List Jobs with ETag
```bash
curl -X GET http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "If-None-Match: \"abc123\""
```

### 4. Create Task
```bash
curl -X POST http://localhost:8000/api/v1/collab/tasks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Review PR #123", "description": "Review frontend changes"}'
```

---

## Monitoring

The API includes structured logging with:
- Request/response logging
- Error tracking with stack traces
- Performance metrics
- Correlation IDs for tracing

Logs are written to `.devlogs/orch-{orch_id}.log` in development.