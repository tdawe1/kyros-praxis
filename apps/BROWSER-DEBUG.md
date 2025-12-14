# Browser Debugging Guide

## Issue
- "Failed to fetch" error in console
- "Incorrect password" when logging in through GUI
- But curl tests work fine

## Quick Diagnosis

### Step 1: Open Test Page
**URL**: http://localhost:3000/test-api.html

This will test:
1. Health check endpoint
2. Auth me endpoint
3. Login functionality
4. Post-login auth check

Watch the results on the page.

### Step 2: Check Browser Console
**Open DevTools** (F12) → **Console** tab

Look for:
- Any "Failed to fetch" errors
- CORS errors
- Network errors
- Red error messages

### Step 3: Check Network Tab
**Open DevTools** (F12) → **Network** tab

1. Refresh the page (Ctrl+R)
2. Try to login
3. Look at the requests:
   - Do they go to `/api/...` or something else?
   - What's the status code? (401, 404, 500?)
   - Check the **Preview** tab of failed requests

### Step 4: Check Cookies
**Open DevTools** (F12) → **Application** tab → **Cookies** → **http://localhost:3000**

After login, you should see:
- `access_token` (HttpOnly)
- `refresh_token` (HttpOnly)

If cookies are missing, the login might not be working.

---

## Common Issues & Fixes

### Issue: "Failed to fetch"

**Cause**: Browser can't reach the API

**Check**:
```bash
# Is API running?
curl http://localhost:8001/health

# Is console running?
curl http://localhost:3000

# Is proxy working?
curl http://localhost:3000/api/health
```

**Fix**:
```bash
# Restart both servers
pkill -f "uvicorn"; pkill -f "next dev"
sleep 2

# Start API
cd /home/thomas/kyros-praxis/apps/api
/home/thomas/kyros-praxis/.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8001 &

# Start Console
cd /home/thomas/kyros-praxis/apps/console
npm run dev &
```

### Issue: "Incorrect password" in GUI (but curl works)

**Possible Causes**:
1. Frontend sending different data format
2. Extra whitespace in password field
3. Browser cache/cookies interfering
4. Extension intercepting requests

**Fixes to Try**:

**A. Clear Browser Cache**
- Ctrl+Shift+Delete → Clear cache
- Or use Incognito mode (Ctrl+Shift+N)

**B. Hard Refresh**
- Ctrl+Shift+R (or Cmd+Shift+R on Mac)

**C. Check DevTools Network Tab**
- Look at the POST /api/auth/login request
- Check the **Payload** tab
- Verify email and password are correct

**D. Try Different Browser**
- Chrome/Firefox/Safari
- Incognito mode

**E. Disable Browser Extensions**
- Extensions can intercept fetch requests
- Try with extensions disabled

### Issue: CORS Errors

**Symptoms**: Console shows errors like "CORS policy blocked"

**Fix**:
```bash
# Check API .env has correct CORS
cd /home/thomas/kyros-praxis/apps/api
grep CORS_ALLOW_ORIGINS .env
# Should be: CORS_ALLOW_ORIGINS=["http://localhost:3000"]

# If wrong, fix it:
# Edit .env and set: CORS_ALLOW_ORIGINS=["http://localhost:3000"]

# Restart API
pkill -f "uvicorn"
/home/thomas/kyros-praxis/.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Issue: Proxy Not Working

**Symptoms**: Requests go to `http://localhost:8001/...` instead of `/api/...`

**Fix**:
```bash
# Check console .env.local
cd /home/thomas/kyros-praxis/apps/console
cat .env.local
# Should have: NEXT_PUBLIC_API_BASE_URL=/api

# Clear cache and restart
rm -rf .next
npm run dev
```

---

## Manual Login Test (Browser Console)

Open http://localhost:3000, then open **DevTools Console** and run:

```javascript
// Test login
fetch('/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  credentials: 'include',
  body: JSON.stringify({
    email: 'admin@example.com',
    password: 'Admin123!'
  })
})
.then(r => {
  console.log('Status:', r.status);
  return r.json();
})
.then(data => {
  console.log('Response:', data);
})
.catch(err => {
  console.error('Error:', err);
});

// Then check if logged in
fetch('/api/auth/me', { credentials: 'include' })
  .then(r => r.json())
  .then(console.log);
```

---

## Still Not Working?

### Collect Debugging Info

Run these and send the output:

```bash
# 1. Server status
pgrep -f "uvicorn" && echo "API running" || echo "API not running"
pgrep -f "next dev" && echo "Console running" || echo "Console not running"

# 2. Test direct API
curl -v http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Admin123!"}'

# 3. Test through proxy
curl -v http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Admin123!"}'

# 4. Check API logs
tail -50 /tmp/api-fresh.log | grep "POST /auth/login"

# 5. Check console logs
tail -50 /tmp/console-rebuild.log | grep -i error
```

### In Browser DevTools

1. **Network Tab**:
   - Screenshot of failed /api/auth/login request
   - Check **Headers**, **Payload**, **Preview** tabs

2. **Console Tab**:
   - Copy any error messages
   - Include full stack traces

3. **Application Tab** → **Cookies**:
   - Screenshot of cookies (if any)

---

## Working Configuration

If everything is working, you should see:

**Terminal Tests**:
```bash
$ curl http://localhost:8001/health
{"status":"ok",...}

$ curl http://localhost:3000/api/health
{"status":"ok",...}

$ curl -X POST http://localhost:3000/api/auth/login -d '...'
{"access_token":"...","refresh_token":"..."}
```

**Browser** (http://localhost:3000/login):
- Login form appears
- No errors in Console tab
- Login succeeds → redirects to dashboard
- Network tab shows `/api/auth/login` → 200 OK
- Cookies tab shows `access_token` and `refresh_token`

---

## Test Page Results

After opening http://localhost:3000/test-api.html, you should see:

```
Starting API tests...

1. Testing /api/health...
   ✅ Status: 200
   Response: {"status":"ok",...}

2. Testing /api/auth/me (unauthenticated)...
   Status: 401
   Response: {"detail":"Not authenticated"}

3. Testing login...
   Status: 200
   Response: {"access_token":"...","refresh_token":"..."}

4. Testing /api/auth/me (authenticated)...
   Status: 200
   Response: {"email":"admin@example.com",...}

Tests complete!
```

If you see different results, there's an issue.
