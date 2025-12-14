# Multi-Agent Orchestration API Reference

**Version**: 0.3.0  
**Base URL**: `http://localhost:8000`

---

## Projects

### Create Project
```http
POST /projects
Content-Type: application/json

{
  "name": "Build REST API",
  "description": "Multi-agent project to build a REST API"
}
```

**Response**:
```json
{
  "id": "uuid",
  "name": "Build REST API",
  "description": "...",
  "status": "planning",
  "created_by": null,
  "created_at": "2025-01-12T...",
  "updated_at": "2025-01-12T..."
}
```

### List Projects
```http
GET /projects
```

### Get Project
```http
GET /projects/{project_id}
```

### Update Project
```http
PATCH /projects/{project_id}
Content-Type: application/json

{
  "status": "executing"
}
```

### Delete Project
```http
DELETE /projects/{project_id}
```

### Get Project Dashboard
```http
GET /projects/{project_id}/dashboard
```

**Response**:
```json
{
  "project": {...},
  "tasks": [...],
  "active_runs": 2,
  "completed_tasks": 3,
  "total_tasks": 5,
  "artifacts": [...]
}
```

---

## Tasks

### Create Task
```http
POST /projects/{project_id}/tasks
Content-Type: application/json

{
  "title": "Database Schema",
  "description": "Design and implement database schema",
  "priority": "P0",
  "dependencies": []
}
```

**Priority Levels**: `P0` (critical), `P1` (high), `P2` (normal)

### List Tasks
```http
GET /projects/{project_id}/tasks
```

### Get Task
```http
GET /projects/{project_id}/tasks/{task_id}
```

### Update Task
```http
PATCH /projects/{project_id}/tasks/{task_id}
Content-Type: application/json

{
  "status": "completed",
  "dependencies": ["other-task-id"]
}
```

**Task Statuses**: `queued`, `running`, `completed`, `failed`, `blocked`, `cancelled`

---

## Batch Runs

### Create Batch Run
```http
POST /batch/runs
Content-Type: application/json

{
  "project_id": "uuid",
  "crew_id": "spec_to_tasks",
  "tasks": [
    {
      "title": "Task 1",
      "description": "First task",
      "priority": "P0"
    },
    {
      "title": "Task 2",
      "description": "Second task",
      "priority": "P1",
      "dependencies": ["task-1-id"]
    }
  ]
}
```

**Response**:
```json
{
  "batch_id": "uuid",
  "project_id": "uuid",
  "tasks": [...],
  "crew_runs": [
    {
      "task_id": "uuid",
      "status": "queued"
    }
  ]
}
```

### Get Batch Status
```http
GET /batch/runs/{batch_id}/status
```

### Cancel Batch
```http
POST /batch/cancel/{batch_id}
```

---

## Shared Memory

### Set Memory Value
```http
POST /memory/set
Content-Type: application/json

{
  "project_id": "uuid",
  "key": "schema_ready",
  "value": {
    "status": "completed",
    "file": "schema.sql"
  },
  "ttl": 3600
}
```

**TTL**: Optional time-to-live in seconds

### Get Memory Value
```http
POST /memory/get
Content-Type: application/json

{
  "project_id": "uuid",
  "key": "schema_ready"
}
```

**Response**:
```json
{
  "key": "schema_ready",
  "value": {
    "status": "completed",
    "file": "schema.sql"
  }
}
```

### Get All Memory
```http
GET /memory/{project_id}/all
```

**Response**:
```json
{
  "schema_ready": {...},
  "auth_code": {...},
  "api_spec": {...}
}
```

### Delete Memory Key
```http
DELETE /memory/{project_id}/{key}
```

---

## Memory Events

### Publish Event
```http
POST /memory/publish
Content-Type: application/json

{
  "project_id": "uuid",
  "event_type": "task_completed",
  "payload": {
    "task_id": "uuid",
    "artifacts": ["file1.py", "file2.py"]
  }
}
```

### Subscribe to Events (SSE)
```http
GET /memory/{project_id}/events?since_id=0
```

**Response** (Server-Sent Events):
```
event: message
data: {"id": 1, "project_id": "...", "event_type": "task_completed", "payload": {...}}

event: message
data: {"id": 2, "project_id": "...", "event_type": "memory_updated", "payload": {...}}
```

**Usage**:
```javascript
const eventSource = new EventSource('/memory/{project_id}/events');
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.event_type, data.payload);
};
```

---

## Crew Runs (Existing)

### Create Run
```http
POST /crews/runs
Content-Type: application/json

{
  "crew_id": "spec_to_tasks",
  "input": {
    "prompt": "Build a REST API"
  }
}
```

### Get Run
```http
GET /crews/runs/{run_id}
```

### Cancel Run
```http
POST /crews/runs/{run_id}/cancel
Content-Type: application/json

{
  "reason": "User requested cancellation"
}
```

### Subscribe to Run Events (SSE)
```http
GET /crews/runs/{run_id}/events
```

---

## Authentication (Existing)

### Register
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "securepassword"
}
```

### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=username&password=securepassword
```

**Response**:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### Get Current User
```http
GET /auth/me
Authorization: Bearer eyJ...
```

---

## Event Types

### Memory Events
- `memory_updated` - Key-value updated
- `task_created` - New task added
- `task_completed` - Task finished
- `task_escalated` - Task needs human review
- `batch_started` - Batch run initiated

### Crew Run Events  
- `started` - Run began
- `agent_started` - Agent began work
- `agent_completed` - Agent finished
- `tool_called` - Agent used a tool
- `completed` - Run finished
- `failed` - Run failed
- `canceled` - Run canceled

---

## Workflow Pipeline

When a task is started (via batch run or manually), it goes through:

### Stage 1: Orchestrator
- **Crew**: `spec_to_tasks`
- **Input**: Task description
- **Output**: Detailed implementation plan

### Stage 2: Implementer
- **Crew**: `code_implementer` (needs to be created)
- **Input**: Plan from orchestrator
- **Output**: Generated code/artifacts

### Stage 3: Critic
- **Crew**: `code_critic` (needs to be created)
- **Input**: Implementation
- **Output**: Feedback with status
  - `approved` → Store artifacts, complete task
  - `changes_requested` → Refine and retry (max 3x)
  - `rejected` → Escalate to human

---

## Example: Complete Workflow

### 1. Create Project
```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Build Todo API",
    "description": "RESTful API for todo management"
  }'
```

### 2. Create Batch Run
```bash
curl -X POST http://localhost:8000/batch/runs \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "PROJECT_ID",
    "crew_id": "spec_to_tasks",
    "tasks": [
      {
        "title": "Database Schema",
        "description": "Design schema for todos",
        "priority": "P0"
      },
      {
        "title": "CRUD Endpoints",
        "description": "Implement create, read, update, delete",
        "priority": "P1"
      }
    ]
  }'
```

### 3. Monitor Progress
```bash
# Watch events
curl -N http://localhost:8000/memory/PROJECT_ID/events

# Check dashboard
curl http://localhost:8000/projects/PROJECT_ID/dashboard
```

### 4. Agents Coordinate
Agent 1 (Schema):
```bash
# Sets memory when done
POST /memory/set
{
  "project_id": "...",
  "key": "schema_ready",
  "value": {"file": "schema.sql"}
}
```

Agent 2 (Endpoints):
```bash
# Reads memory to check dependency
POST /memory/get
{
  "project_id": "...",
  "key": "schema_ready"
}
# Proceeds when schema is ready
```

---

## Error Responses

### 404 Not Found
```json
{
  "detail": "Project not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## OpenAPI Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## Rate Limits

None currently implemented, but recommended for production:
- 100 requests/minute per IP
- 1000 requests/hour per user
- 10 concurrent SSE connections per project

---

## WebSocket Support

Not yet implemented, but planned for Phase 3:
- Real-time agent status updates
- Live artifact preview
- Interactive critic feedback
- Multi-user collaboration

---

## Security

### Current:
- JWT authentication (optional)
- CORS configured
- SQL injection protection (SQLAlchemy)

### Recommended for Production:
- API key authentication
- Rate limiting
- Request validation
- Input sanitization
- Audit logging
- Encrypted storage for sensitive artifacts

---

**Last Updated**: 2025-01-12  
**API Version**: 0.3.0
