# 🚀 Kyros Praxis - READY FOR TESTING

## ✅ System Status

**Backend API**: http://localhost:8001 ✅  
**Frontend Console**: http://localhost:3000 ✅  
**Proxy Working**: /api/* → backend ✅

---

## 🔐 Login to Test

**Open**: http://localhost:3000/login

**Credentials**:
- Email: `admin@example.com`
- Password: `Admin123!`

*Note: Simplified password. Change after first login in production.*

---

## 🧪 What to Test

### 1. Basic Authentication
- [ ] Login works
- [ ] Dashboard loads after login
- [ ] Logout works
- [ ] Cookies are set (check DevTools → Application → Cookies)

### 2. Security Fixes (These Should Be Fixed)
- [ ] Cannot access projects without login
- [ ] Cannot modify other users' projects
- [ ] Workflow endpoints require auth
- [ ] Run endpoints require auth

### 3. Try These in Browser Console

After logging in, open DevTools Console and run:

```javascript
// Should work (authenticated)
fetch('/api/auth/me')
  .then(r => r.json())
  .then(d => console.log('Me:', d));

// Should work (authenticated)
fetch('/api/projects')
  .then(r => r.json())
  .then(d => console.log('Projects:', d));

// Create a project
fetch('/api/projects', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    name: 'Test Project',
    description: 'Testing from browser'
  })
}).then(r => r.json()).then(d => console.log('Created:', d));
```

### 4. Check Network Tab
- [ ] Requests go to `/api/*` (not `http://localhost:8001/*`)
- [ ] Cookies are sent with requests
- [ ] No CORS errors
- [ ] 401 errors before login, 200 after

---

## 📊 Server Logs

```bash
# API logs
tail -f /tmp/console-final.log

# Console logs
tail -f /tmp/api-fresh.log

# Both
tail -f /tmp/api-fresh.log /tmp/console-final.log
```

---

## 🛑 Stop Servers

```bash
pkill -f "uvicorn app.main:app"
pkill -f "next dev"
```

---

## 🔄 Restart if Needed

```bash
# API
cd /home/thomas/kyros-praxis/apps/api
/home/thomas/kyros-praxis/.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Console
cd /home/thomas/kyros-praxis/apps/console
npm run dev
```

---

## ✅ Known Working

1. ✅ API authentication on all endpoints
2. ✅ Ownership checks for projects
3. ✅ WebSocket authentication (token in URL)
4. ✅ Cookie-based auth (HttpOnly cookies)
5. ✅ CORS configured for localhost:3000
6. ✅ Next.js proxy working

---

## 📖 More Info

- **Full Testing Guide**: `apps/api/TESTING-GUIDE.md`
- **Security Verification**: `apps/SECURITY-VERIFICATION-FINAL.md`
- **API Docs**: http://localhost:8001/docs

---

**Everything is ready!** Open http://localhost:3000 and start testing! 🎉
