# Full Stack Status - Ready for Testing

## ✅ System Status

**Backend API**: http://localhost:8001 ✅ Running  
**Frontend Console**: http://localhost:3000 ✅ Running  
**Database**: PostgreSQL localhost:5432 ✅ Connected

---

## 🔐 Login Credentials

**Email**: `admin@example.com`  
**Password**: `AdminPass123!`  
**Role**: `user`

---

## 🌐 Access Points

### Frontend Console
- **URL**: http://localhost:3000
- **Login Page**: http://localhost:3000/login
- **Dashboard**: http://localhost:3000/dashboard (after login)

### Backend API
- **Health Check**: http://localhost:8001/health
- **API Docs**: http://localhost:8001/docs
- **OpenAPI Spec**: http://localhost:8001/openapi.json

### Proxied API (through Console)
- **Health Check**: http://localhost:3000/api/health
- **Auth Check**: http://localhost:3000/api/auth/me
- **Any endpoint**: http://localhost:3000/api/{endpoint}

---

## 🧪 Quick Tests

### Test 1: Direct API Access
```bash
curl http://localhost:8001/health
# Expected: {"status":"ok",...}
```

### Test 2: Proxied API Access (Console → API)
```bash
curl http://localhost:3000/api/health
# Expected: {"status":"ok",...}
```

### Test 3: Unauthenticated Access (Should Return 401)
```bash
curl http://localhost:3000/api/auth/me
# Expected: {"detail":"Authentication required"}
```

### Test 4: Login via Console Proxy
```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "email": "admin@example.com",
    "password": "AdminPass123!"
  }'
# Expected: {"access_token":"...","refresh_token":"...","token_type":"bearer"}
```

### Test 5: Authenticated Access with Cookies
```bash
curl -b cookies.txt http://localhost:3000/api/auth/me
# Expected: {"email":"admin@example.com","username":"admin",...}
```

---

## 🎯 Testing Security Fixes

### Browser Testing (Recommended)

1. **Open**: http://localhost:3000/login
2. **Login** with: `admin@example.com` / `AdminPass123!`
3. **Open DevTools** → Network tab
4. **Verify**:
   - Requests go to `/api/...` (proxied)
   - Cookies are set: `access_token`, `refresh_token`
   - Auth header or cookies are sent with requests

### Test Unauthenticated Endpoints (Should Fail)

Open DevTools Console and run:
```javascript
// Should all return 401 errors
fetch('/api/projects/test/generate', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({prompt: 'test'})
}).then(r => r.json()).then(console.log);

fetch('/api/crews/runs/test-run')
  .then(r => r.json()).then(console.log);
```

### Test Authenticated Endpoints (Should Work After Login)

```javascript
// After logging in, these should work
fetch('/api/projects')
  .then(r => r.json()).then(console.log);

fetch('/api/auth/me')
  .then(r => r.json()).then(console.log);
```

---

## 📊 Configuration Summary

### API Configuration (`apps/api/.env`)
```
DATABASE_URL=postgresql+asyncpg://kyros:kyros@localhost:5432/kyros
JWT_SECRET_KEY=<configured>
CORS_ALLOW_ORIGINS=["http://localhost:3000"]
KYROS_ENV=dev
COOKIE_SECURE=false  ← Set to false for HTTP development
COOKIE_HTTPONLY=true
COOKIE_SAMESITE=lax
```

### Console Configuration (`apps/console/.env.local`)
```
NEXT_PUBLIC_API_BASE_URL=/api
NEXT_PUBLIC_TERMINAL_WS_URL=ws://localhost:8001/ws/terminal
```

### Proxy Configuration (`apps/console/next.config.js`)
```javascript
// Proxies /api/* → http://localhost:8001/*
async rewrites() {
  return [{
    source: '/api/:path*',
    destination: 'http://localhost:8001/:path*',
  }];
}
```

---

## 🔍 Troubleshooting

### Console Not Loading
```bash
# Check if running
curl http://localhost:3000

# Check logs
tail -f /tmp/console-dev.log

# Restart
pkill -f "next dev"
cd /home/thomas/kyros-praxis/apps/console && npm run dev
```

### API Not Responding
```bash
# Check if running
curl http://localhost:8001/health

# Check logs
tail -f /tmp/api-dev.log

# Restart
pkill -f "uvicorn"
cd /home/thomas/kyros-praxis/apps/api
/home/thomas/kyros-praxis/.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Proxy Not Working (404 on /api/*)
1. **Check next.config.js** is correct
2. **Restart console** (required after config changes)
3. **Try direct URL**: http://localhost:8001/health
4. **Bypass proxy**: Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8001` in console/.env.local

### Cookies Not Being Set
1. **Check COOKIE_SECURE**: Should be `false` in apps/api/.env for HTTP
2. **Check CORS**: Should include `http://localhost:3000`
3. **Check browser**: DevTools → Application → Cookies → localhost:3000
4. **Try incognito**: Rules out browser extension interference

### Network Errors
1. **Check CORS**: Browser console shows CORS errors?
2. **Check proxy**: Network tab shows requests to `/api/*`?
3. **Check cookies**: Cookies tab shows access_token?
4. **Disable extensions**: Try incognito mode

---

## 📝 Server Management

### Start Both Servers
```bash
# Terminal 1 - API
cd /home/thomas/kyros-praxis/apps/api
/home/thomas/kyros-praxis/.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Terminal 2 - Console
cd /home/thomas/kyros-praxis/apps/console
npm run dev
```

### Stop Both Servers
```bash
pkill -f "uvicorn app.main:app"
pkill -f "next dev"
```

### View Logs
```bash
# API logs
tail -f /tmp/api-dev.log

# Console logs  
tail -f /tmp/console-dev.log

# Both
tail -f /tmp/api-dev.log /tmp/console-dev.log
```

---

## ✅ What's Working

1. ✅ **API Authentication** - All endpoints require auth
2. ✅ **Ownership Checks** - Users can only modify their own projects
3. ✅ **WebSocket Security** - Auth checked before connection
4. ✅ **Cookie Authentication** - HttpOnly cookies working
5. ✅ **CORS Configuration** - Console can access API
6. ✅ **Proxy Setup** - Next.js proxy working (/api/* → backend)

---

## 🎯 Next Steps

1. **Open browser**: http://localhost:3000
2. **Login**: admin@example.com / AdminPass123!
3. **Test features**: Create projects, tasks, etc.
4. **Verify security**: Check DevTools for auth headers/cookies
5. **Report issues**: Check logs and provide details

---

**System Ready!** 🚀  
**Last Updated**: January 2024
