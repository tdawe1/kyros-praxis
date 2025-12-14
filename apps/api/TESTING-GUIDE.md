# Kyros Praxis API - Testing Guide

## Quick Start

### 1. Start the API Server

```bash
cd /home/thomas/kyros-praxis/apps/api
./start-local.sh
```

The server will start on: **http://localhost:8001**

### 2. Verify Server is Running

```bash
curl http://localhost:8001/health
```

Expected response:
```json
{
  "status": "ok",
  "env": "dev",
  "features": {
    "rate_limiting": true,
    "metrics": true,
    "caching": null,
    "background_jobs": true
  }
}
```

---

## Security Testing

### Phase 1: Test Unauthenticated Requests (Should All Return 401)

```bash
# Test 1: Project update without auth
curl -X PATCH http://localhost:8001/projects/test-id \
  -H "Content-Type: application/json" \
  -d '{"name":"Hacked"}'
# Expected: {"detail":"Authentication required"}

# Test 2: Workflow generate without auth
curl -X POST http://localhost:8001/projects/test-id/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test"}'
# Expected: {"detail":"Authentication required"}

# Test 3: Workflow approve without auth
curl -X POST http://localhost:8001/projects/test-id/approve \
  -H "Content-Type: application/json" \
  -d '{"approved":true,"specification":{}}'
# Expected: {"detail":"Authentication required"}

# Test 4: Run retrieval without auth
curl http://localhost:8001/crews/runs/test-run-id
# Expected: {"detail":"Authentication required"}

# Test 5: Run cancellation without auth
curl -X POST http://localhost:8001/crews/runs/test-run-id/cancel
# Expected: {"detail":"Authentication required"}

# Test 6: Memory set without auth
curl -X POST http://localhost:8001/memory/set \
  -H "Content-Type: application/json" \
  -d '{"project_id":"test","key":"k","value":"v"}'
# Expected: {"detail":"Authentication required"}

# Test 7: Batch runs without auth
curl -X POST http://localhost:8001/batch/runs \
  -H "Content-Type: application/json" \
  -d '{"project_id":"test","tasks":[]}'
# Expected: {"detail":"Authentication required"}
```

### Phase 2: Test Authenticated Requests

#### Step 1: Register a User

```bash
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
```

Expected response:
```json
{
  "id": "...",
  "username": "testuser",
  "email": "test@example.com",
  "role": "user",
  "active": true
}
```

#### Step 2: Login and Get Token

```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
```

Expected response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Save the access token:**
```bash
export TOKEN="eyJ..."  # Replace with actual token from login
```

#### Step 3: Create a Project

```bash
curl -X POST http://localhost:8001/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Test Project",
    "description": "Testing security features"
  }'
```

Expected response (201):
```json
{
  "id": "...",
  "name": "Test Project",
  "description": "Testing security features",
  "status": "planning",
  "created_by": "...",
  "created_at": "...",
  "updated_at": "..."
}
```

**Save the project ID:**
```bash
export PROJECT_ID="..."  # Replace with actual ID from response
```

#### Step 4: Test Authenticated Operations

```bash
# List projects (should only show user's projects)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/projects

# Update own project (should succeed)
curl -X PATCH http://localhost:8001/projects/$PROJECT_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"Updated Project Name"}'

# Get project dashboard (should succeed)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/projects/$PROJECT_ID/dashboard

# Create task in project (should succeed)
curl -X POST http://localhost:8001/projects/$PROJECT_ID/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Test Task",
    "description": "Testing task creation",
    "priority": "P1"
  }'

# Create crew run (should succeed)
curl -X POST http://localhost:8001/crews/runs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "crew_id": "test-crew",
    "input": {"test": "data"}
  }'
```

### Phase 3: Test Ownership Checks

#### Step 1: Register Second User

```bash
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "otheruser",
    "email": "other@example.com",
    "password": "OtherPass123!"
  }'
```

#### Step 2: Login as Second User

```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "other@example.com",
    "password": "OtherPass123!"
  }'
```

**Save the second user's token:**
```bash
export TOKEN2="eyJ..."  # Replace with actual token
```

#### Step 3: Try to Access First User's Project (Should Fail with 403)

```bash
# Try to update another user's project (should fail with 403)
curl -X PATCH http://localhost:8001/projects/$PROJECT_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN2" \
  -d '{"name":"Hacked Project"}'
# Expected: {"detail":"Not authorized to modify this project"}

# Try to delete another user's project (should fail with 403)
curl -X DELETE http://localhost:8001/projects/$PROJECT_ID \
  -H "Authorization: Bearer $TOKEN2"
# Expected: {"detail":"Not authorized to delete this project"}

# Try to generate code for another user's project (should fail with 403)
curl -X POST http://localhost:8001/projects/$PROJECT_ID/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN2" \
  -d '{"prompt":"test"}'
# Expected: {"detail":"Not authorized to generate code for this project"}
```

---

## WebSocket Testing

### Requirements
Install `wscat` for WebSocket testing:
```bash
npm install -g wscat
```

### Test 1: Connect Without Token (Should Fail)

```bash
wscat -c ws://localhost:8001/ws/terminal
# Expected: Connection closed with code 1008 "Authentication required"
```

### Test 2: Connect With Invalid Token (Should Fail)

```bash
wscat -c "ws://localhost:8001/ws/terminal?token=invalid"
# Expected: Connection closed with code 1008 "Invalid token"
```

### Test 3: Connect With Valid Token (Should Succeed)

```bash
# First, get a valid token (reuse $TOKEN from above)
wscat -c "ws://localhost:8001/ws/terminal?token=$TOKEN"

# Expected: Connection accepted, auth_success message received
# You should get a working terminal session
```

---

## API Documentation

### Interactive API Docs

Visit: **http://localhost:8001/docs**

This provides a Swagger UI where you can:
- View all endpoints
- Test endpoints interactively
- See request/response schemas
- Use "Authorize" button to set Bearer token

### Alternative Docs

Visit: **http://localhost:8001/redoc**

---

## Troubleshooting

### Server Won't Start

1. **Check if port 8001 is in use:**
   ```bash
   lsof -i:8001
   kill $(lsof -ti:8001)  # Kill process using port
   ```

2. **Check PostgreSQL:**
   ```bash
   pg_isready -h localhost -p 5432
   sudo systemctl status postgresql
   ```

3. **Check environment:**
   ```bash
   cd /home/thomas/kyros-praxis/apps/api
   cat .env | grep DATABASE_URL
   ```

4. **Check logs:**
   ```bash
   tail -50 /tmp/api-server.log
   ```

### Database Errors

1. **Apply migrations:**
   ```bash
   cd /home/thomas/kyros-praxis/apps/api
   /home/thomas/kyros-praxis/.venv/bin/alembic upgrade head
   ```

2. **Reset database (DESTRUCTIVE):**
   ```bash
   psql -h localhost -U kyros -d kyros -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
   /home/thomas/kyros-praxis/.venv/bin/alembic upgrade head
   ```

### 401 Errors Despite Valid Token

1. **Check token expiry:**
   - Default expiry: 24 hours (1440 minutes)
   - Login again to get fresh token

2. **Check token format:**
   - Must be: `Authorization: Bearer <token>`
   - NOT: `Authorization: <token>`

3. **Check token type:**
   - Use `access_token`, not `refresh_token`

### Import Errors

```bash
cd /home/thomas/kyros-praxis
source .venv/bin/activate
cd apps/api
pip install -r requirements.txt
```

---

## Quick Test Script

Save this as `test-security.sh`:

```bash
#!/bin/bash
set -e

API="http://localhost:8001"

echo "=== Testing Security ==="
echo ""

# Test unauthenticated (should fail)
echo "1. Testing unauthenticated project update..."
RESPONSE=$(curl -s -X PATCH $API/projects/test \
  -H "Content-Type: application/json" \
  -d '{"name":"test"}')
if echo "$RESPONSE" | grep -q "Authentication required"; then
    echo "✅ PASS - Returns 401"
else
    echo "❌ FAIL - Did not require auth"
    exit 1
fi

# Register user
echo "2. Registering test user..."
curl -s -X POST $API/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"Test123!"}' > /dev/null

# Login
echo "3. Logging in..."
TOKEN=$(curl -s -X POST $API/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test123!"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    echo "✅ PASS - Got token"
else
    echo "❌ FAIL - Login failed"
    exit 1
fi

# Create project
echo "4. Creating project with auth..."
PROJECT=$(curl -s -X POST $API/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"Test","description":"Test"}')

if echo "$PROJECT" | grep -q '"id"'; then
    echo "✅ PASS - Project created"
    PROJECT_ID=$(echo "$PROJECT" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)
else
    echo "❌ FAIL - Could not create project"
    exit 1
fi

# Update own project
echo "5. Updating own project..."
UPDATE=$(curl -s -X PATCH $API/projects/$PROJECT_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"Updated"}')

if echo "$UPDATE" | grep -q "Updated"; then
    echo "✅ PASS - Update succeeded"
else
    echo "❌ FAIL - Update failed"
    exit 1
fi

echo ""
echo "=== All Tests Passed ==="
```

Then run:
```bash
chmod +x test-security.sh
./test-security.sh
```

---

## Stopping the Server

Press **Ctrl+C** in the terminal running the server, or:

```bash
pkill -f "uvicorn app.main:app"
```

---

## Next Steps

After verifying security locally:

1. **Test P2-MEDIUM issues** (if desired)
2. **Deploy to staging** environment
3. **Update frontend** WebSocket clients (breaking change)
4. **Monitor** for auth failures in production

---

**Last Updated**: January 2024  
**Server Version**: 0.3.0
