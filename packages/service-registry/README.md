# Kyros Service Registry Service

## API Specs
- OpenAPI/Swagger: http://localhost:8001/docs.
- Key Endpoints:
  - POST /register: Register service, returns 200. Body: {"id": str, "endpoint": str}. Auth: Bearer JWT.
  - GET /services: List services, returns 200 {services: [...]}. Auth: Bearer.
  - GET /discovery: Discovery, returns 200 {discovery: [...]}. Auth: Bearer.
  - DELETE /unregister/{name}: Deregister, returns 200. Auth: Bearer.
  - GET /health/{name}: Health check, returns 200 {status: "healthy"}. Auth: Bearer.

## Setup and Run Instructions
- Prerequisites: Python 3.11, pip install -r requirements.txt.
- Copy .env.example to .env, set SECRET_KEY=strong_random_key.
- Run: uvicorn main:app --reload --host 0.0.0.0 --port 8001.
- Test: curl -X POST http://localhost:8001/register -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMSJ9.signature" -d '{"id":"svc1","endpoint":"http://test:8000"}' (expect 200), then GET /services.

## Error Handling Guide
- 404 Not Found: ID not registered - Return 404 with detail.
- 409 Conflict: Duplicate ID - Return 409, use ETags for retry (future).
- 401 Unauthorized: Missing token - Enforce on all routes.
- Logs: Add registration events.

## Migration Notes
- Current: In-memory dict. Future: etcd for distributed; add etcd3 client when implemented.
- When etcd added: Set ETCD_HOST=localhost:2379 in .env.