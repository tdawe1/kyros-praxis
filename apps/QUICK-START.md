# Kyros Praxis - Quick Start Guide

## 🚀 System is Running!

**API Server**: http://localhost:8001  
**API Docs**: http://localhost:8001/docs  
**Health Check**: http://localhost:8001/health

---

## 🔐 Admin Login Credentials

**Email**: `admin@example.com`  
**Password**: `AdminPass123!`  
**Role**: `user` (can be upgraded to `admin` if needed)

### Quick Login Test

```bash
# Login and get token
export TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"AdminPass123!"}' \
  | jq -r '.access_token')

echo "Token: ${TOKEN:0:40}..."

# Verify login
curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/auth/me | jq .
```

---

## 🧪 Test Security Fixes

### 1. Test Unauthenticated Access (Should Fail with 401)

```bash
# Workflow generate without auth
curl -X POST http://localhost:8001/projects/test-id/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test"}'
# Expected: {"detail":"Authentication required"}

# Run retrieval without auth
curl http://localhost:8001/crews/runs/test-run
# Expected: {"detail":"Authentication required"}

# Memory access without auth
curl -X POST http://localhost:8001/memory/set \
  -H "Content-Type: application/json" \
  -d '{"project_id":"test","key":"k","value":"v"}'
# Expected: {"detail":"Authentication required"}
```

### 2. Test Authenticated Access (Should Work)

```bash
# Create a project
curl -X POST http://localhost:8001/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "My Test Project",
    "description": "Testing authenticated access"
  }'

# List projects (should show only your projects)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/projects | jq .

# Create a task
PROJECT_ID="..."  # Use ID from project creation above
curl -X POST http://localhost:8001/projects/$PROJECT_ID/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Test Task",
    "description": "Testing task creation",
    "priority": "P1"
  }'
```

### 3. Test Ownership Checks

```bash
# Register a second user
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user2",
    "email": "user2@example.com",
    "password": "User2Pass123!"
  }'

# Login as second user
TOKEN2=$(curl -s -X POST http://localhost:8001/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"user2@example.com","password":"User2Pass123!"}' \
  | jq -r '.access_token')

# Try to update first user's project (should fail with 403)
curl -X PATCH http://localhost:8001/projects/$PROJECT_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN2" \
  -d '{"name":"Hacked"}'
# Expected: {"detail":"Not authorized to modify this project"}
```

---

## 📚 Interactive API Documentation

Visit **http://localhost:8001/docs** in your browser for:
- Complete API reference
- Interactive testing (try endpoints directly)
- Request/response schemas
- Authentication (click "Authorize" button to set Bearer token)

---

## 🛠️ Server Management

### Start Server
```bash
cd /home/thomas/kyros-praxis/apps/api
./start-local.sh
```

### Stop Server
```bash
pkill -f "uvicorn app.main:app"
```

### Check Server Status
```bash
curl http://localhost:8001/health
```

### View Logs
```bash
tail -f /tmp/api-final.log
```

---

## 📖 Full Documentation

- **Testing Guide**: `/home/thomas/kyros-praxis/apps/api/TESTING-GUIDE.md`
- **Admin Setup**: `/home/thomas/kyros-praxis/apps/api/ADMIN-CREDENTIALS.md`
- **Security Verification**: `/home/thomas/kyros-praxis/apps/SECURITY-VERIFICATION-FINAL.md`

---

## ✅ What's Been Fixed

All P1-HIGH security issues have been addressed:

1. ✅ **Workflow endpoints** (generate/approve/regenerate) - Require auth + ownership
2. ✅ **Run endpoints** (get/cancel) - Require authentication
3. ✅ **WebSocket** - Validates token BEFORE accepting connection
4. ✅ **WorkflowStage regression** - Fixed join through CrewRun

---

## 🎯 Next Steps

1. **Test all endpoints** using the commands above
2. **Verify security fixes** are working as expected
3. **Review** the full testing guide if needed
4. **Deploy** to staging once testing is complete

---

**Server Ready!** 🟢
