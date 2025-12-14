# 🌐 Test in Browser - Step by Step

## ✅ System Status

**API**: Running on port 8001  
**Console**: Running on port 3000  
**Credentials**: admin@example.com / Admin123!

---

## 🧪 Step 1: Open Test Page

**URL**: http://localhost:3000/test-api.html

This page will automatically test:
1. ✅ Health check
2. ✅ Auth endpoint (before login)
3. ✅ Login with credentials
4. ✅ Auth endpoint (after login)

**Expected Results**: All 4 tests should pass with status 200

---

## 🔐 Step 2: Try Manual Login

**URL**: http://localhost:3000/login

1. Enter email: `admin@example.com`
2. Enter password: `Admin123!`
3. Click **Login**

### If Login Fails:

**Open DevTools** (Press F12):

#### A. Check Console Tab
Look for:
- ❌ "Failed to fetch" errors
- ❌ CORS errors
- ❌ Any red error messages

#### B. Check Network Tab
1. Find the `POST /api/auth/login` request
2. Click on it
3. Check these tabs:
   - **Headers**: Should show `/api/auth/login`
   - **Payload**: Should have your email/password
   - **Preview**: See the error message
   - **Response**: See what the server said

#### C. Common Errors & Fixes

**"Failed to fetch"**:
```
The browser can't reach the API.
Fix: Restart both servers (see bottom of this file)
```

**Status 401 "Incorrect password"**:
```
Try in DevTools Console:
fetch('/api/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  credentials: 'include',
  body: JSON.stringify({
    email: 'admin@example.com',
    password: 'Admin123!'
  })
}).then(r => r.json()).then(console.log);
```

**Status 404**:
```
The proxy isn't working.
Check: Does the URL show /api/auth/login or http://localhost:8001/auth/login?
If it's 8001, the proxy failed. Restart console.
```

**CORS Error**:
```
The API isn't allowing requests from the console.
Check API logs for CORS errors.
```

---

## 🧪 Step 3: Test After Login

If login succeeds, try these in **DevTools Console**:

```javascript
// Check you're logged in
fetch('/api/auth/me', { credentials: 'include' })
  .then(r => r.json())
  .then(d => console.log('Current user:', d));

// List projects
fetch('/api/projects', { credentials: 'include' })
  .then(r => r.json())
  .then(d => console.log('Projects:', d));

// Create a project
fetch('/api/projects', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  credentials: 'include',
  body: JSON.stringify({
    name: 'Browser Test',
    description: 'Created from DevTools'
  })
}).then(r => r.json()).then(d => console.log('Created:', d));
```

---

## 🍪 Step 4: Check Cookies

**DevTools** → **Application** tab → **Cookies** → **http://localhost:3000**

After successful login, you should see:
- `access_token` (HttpOnly, Secure=false)
- `refresh_token` (HttpOnly, Secure=false)

If cookies are missing, the login didn't work.

---

## 🔄 Restart Servers

If something is wrong, restart both:

```bash
# Stop both
pkill -f "uvicorn app.main:app"
pkill -f "next dev"
sleep 2

# Start API
cd /home/thomas/kyros-praxis/apps/api
/home/thomas/kyros-praxis/.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8001 &

# Start Console  
cd /home/thomas/kyros-praxis/apps/console
npm run dev &

# Wait 20 seconds
sleep 20

# Test
curl http://localhost:8001/health
curl http://localhost:3000/api/health
```

---

## 📊 What to Report

If it's still not working, copy these:

### 1. Test Page Results
- Open http://localhost:3000/test-api.html
- Copy all the text from the page

### 2. DevTools Console Errors
- F12 → Console tab
- Copy any red errors

### 3. Failed Request Details
- F12 → Network tab
- Find the failed request (red)
- Right-click → Copy → Copy as cURL

### 4. Cookies
- F12 → Application → Cookies → localhost:3000
- Screenshot or list what cookies you see

---

## ✅ Success Looks Like

**Test Page**: All 4 tests pass  
**Login**: Redirects to dashboard  
**DevTools Console**: No errors  
**DevTools Network**: `/api/auth/login` shows 200 OK  
**DevTools Cookies**: Shows access_token and refresh_token

---

**Start here**: http://localhost:3000/test-api.html
