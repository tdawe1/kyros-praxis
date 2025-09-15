# Quick Start — Orchestrator Steel Thread

This guide gets the backend steel thread running locally and shows how to use ETag and SSE endpoints.

Prereqs: Python 3.11+, curl, jq (for parsing JSON in shell examples).

1) Start the API
- Terminal A
  - `export SECRET_KEY=dev-secret`
  - `uvicorn services.orchestrator.main:app --reload --port 8000`

2) Seed a user and get a token
```bash
python - <<'PY'
from services.orchestrator.database import SessionLocal, engine
from services.orchestrator.models import Base, User
from services.orchestrator.auth import pwd_context
Base.metadata.create_all(bind=engine)
s = SessionLocal()
if not s.query(User).filter(User.email=='dev@example.com').first():
    s.add(User(email='dev@example.com', password_hash=pwd_context.hash('password')))
    s.commit()
s.close()
PY

TOKEN=$(curl -s http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"dev@example.com","password":"password"}' | jq -r .access_token)
echo "$TOKEN"
```

3) Create a task and list with ETag/304
```bash
curl -s http://localhost:8000/api/v1/collab/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Demo","description":"hello"}' | jq

curl -i http://localhost:8000/api/v1/collab/state/tasks
# Copy ETag value (quoted) and then:
ETAG='"paste-etag-here"'
curl -i http://localhost:8000/api/v1/collab/state/tasks -H "If-None-Match: $ETAG"
```

4) Events SSE: append and tail
```bash
curl -i http://localhost:8000/api/v1/events \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"event":"demo","target":"x","details":{"k":"v"}}'

# Backlog only once (exits after emitting stored events)
curl -N -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/events/tail?once=1"
```

5) Focused tests
```bash
export SECRET_KEY=test-secret
make -C services/orchestrator test-thread
make -C services/orchestrator test-events
```

Notes
- All orchestrator endpoints are prefixed by `/api/v1` except `/auth/login`.
- Task list returns quoted ETag and supports `If-None-Match → 304`.
- SSE tail supports `?once=1` to flush backlog and end (test-friendly).

