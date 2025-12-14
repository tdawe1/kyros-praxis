# Authentication Testing Guide

**Quick Start**: How to test your new authentication system

---

## Prerequisites

### 1. Check Servers Are Running

**Backend** (API):
```bash
cd /home/thomas/kyros-praxis/apps/api
../../.venv/bin/uvicorn app.main:app --reload --port 8000
```

**Frontend** (Console):
```bash
cd /home/thomas/kyros-praxis/apps/console
npm run dev
```

You should see:
- Backend: `http://localhost:8000` (API)
- Frontend: `http://localhost:3000` (Web UI)

---

## Test User Accounts

### Option 1: Use Existing Test User

**Email**: `test@example.com`  
**Password**: `testpass123`

### Option 2: Create New User via API

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "myuser",
    "email": "myuser@example.com",
    "password": "mypassword123"
  }'
```

### Option 3: Create User via Python

```bash
cd /home/thomas/kyros-praxis/apps/api
../../.venv/bin/python << 'PYEOF'
import asyncio
from app.db.session import AsyncSessionLocal
from app.db.models import User
from app.auth import hash_password
from uuid import uuid4

async def create_user():
    async with AsyncSessionLocal() as session:
        user = User(
            id=str(uuid4()),
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("testpass123"),
            role="user",
            active=True
        )
        session.add(user)
        await session.commit()
        print(f"✅ Created user: {user.email}")

asyncio.run(create_user())
PYEOF
```

---

## Testing Steps

### 1. Open Browser and Navigate to Login

Open your browser and go to:
```
http://localhost:3000/login
```

### 2. Open DevTools (IMPORTANT!)

**Before logging in**, open browser DevTools:

**Chrome/Edge/Brave**:
- Press `F12` OR
- Right-click → "Inspect" OR
- Menu → More Tools → Developer Tools

**Firefox**:
- Press `F12` OR
- Menu → Web Developer → Toggle Tools

**Safari**:
- Safari → Settings → Advanced → "Show Develop menu"
- Press `Cmd+Option+I`

### 3. Navigate to Application/Storage Tab

In DevTools:
- **Chrome/Edge/Brave**: Click "Application" tab
- **Firefox**: Click "Storage" tab
- **Safari**: Click "Storage" tab

Then expand "Cookies" in the left sidebar and click on `http://localhost:3000`

---

## Test Scenarios

### Test 1: Login and Cookie Creation ✅

**What to do**:
1. Enter email: `test@example.com`
2. Enter password: `testpass123`
3. Click "Login"

**What to check in DevTools → Cookies**:

You should see **two cookies** appear:

| Cookie Name | Value | HttpOnly | Secure | SameSite | Max-Age |
|-------------|-------|----------|--------|----------|---------|
| `access_token` | eyJ... | ✅ | ✅ | Lax | 900 (15 min) |
| `refresh_token` | eyJ... | ✅ | ✅ | Lax | 604800 (7 days) |

**✅ Success indicators**:
- Both cookies present
- HttpOnly flag is checked (you can't see the value in JavaScript console)
- Secure flag is checked (will be used in production with HTTPS)
- SameSite is "Lax" (CSRF protection)
- Redirected to dashboard/main page

**❌ Failure indicators**:
- No cookies appear
- Error message shown
- Still on login page

---

### Test 2: Authenticated Navigation ✅

**What to do**:
1. After logging in, navigate around the app
2. Click different pages/sections

**What to check**:
- Pages load correctly
- User data displays (your username/email)
- No "Not authenticated" errors
- Cookies remain in DevTools

**✅ Success**: App works normally, authenticated content displays

---

### Test 3: Cookie Reading in Console (Security Check) 🔒

**What to do**:
1. While logged in, open DevTools → Console tab
2. Type: `document.cookie`
3. Press Enter

**What to check**:
```javascript
document.cookie
// Should return: "" (empty string) or cookies WITHOUT access_token/refresh_token
```

**✅ Success**: You **cannot** see `access_token` or `refresh_token` in the output
- This proves HttpOnly is working (JavaScript cannot access tokens)
- This prevents XSS attacks

**❌ Failure**: If you see `access_token=eyJ...` in the output
- HttpOnly is NOT working (security issue)

---

### Test 4: Auto-Refresh (Wait 10 Minutes) 🔄

**What to do**:
1. Stay logged in and leave the page open
2. Wait 10+ minutes (or modify the interval for faster testing)
3. Watch DevTools → Network tab

**What to check**:
- After ~10 minutes, you should see a request to `/auth/refresh`
- New cookies are set (token rotation)
- You remain logged in

**✅ Success**: Automatic refresh happens, no logout

---

### Test 5: Logout ✅

**What to do**:
1. Click the "Logout" button
2. Watch DevTools → Cookies

**What to check**:
- Both cookies (`access_token` and `refresh_token`) disappear
- Redirected to login page
- Cannot access authenticated pages

**✅ Success**: Cookies cleared, logged out completely

---

### Test 6: Manual Cookie Deletion (Security Test) 🔒

**What to do**:
1. Log in successfully
2. In DevTools → Application/Storage → Cookies
3. Right-click each cookie → Delete
4. Try to navigate to an authenticated page

**What to check**:
- App detects you're not authenticated
- Redirected to login page
- Cannot access protected content

**✅ Success**: App correctly handles missing cookies

---

### Test 7: Unauthenticated Access (Security Test) 🔒

**What to do**:
1. Open a new incognito/private browser window
2. Go to `http://localhost:3000/dashboard` (or any protected route)
3. Don't log in

**What to check**:
- Redirected to login page
- Cannot see protected content

**✅ Success**: Unauthenticated users blocked from protected pages

---

### Test 8: WebSocket Terminal (Advanced) 🖥️

**What to do**:
1. Log in successfully
2. Navigate to Terminal page
3. Open DevTools → Network tab
4. Filter by "WS" (WebSocket)

**What to check**:
- Request to `/auth/ws-token` succeeds
- WebSocket connection established
- Terminal commands work

**✅ Success**: Terminal connects and works

---

## API Testing (curl)

### Test Login via curl

```bash
# Login and save cookies
curl -c /tmp/cookies.txt -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

**Expected response**:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Test Authenticated Request

```bash
# Use cookies to access protected endpoint
curl -b /tmp/cookies.txt http://localhost:8000/auth/me
```

**Expected response**:
```json
{
  "email": "test@example.com",
  "username": "testuser",
  "id": "...",
  "role": "user",
  "active": true,
  "created_at": "2025-10-13T..."
}
```

### Test Unauthenticated Request

```bash
# Without cookies (should fail)
curl http://localhost:8000/auth/me
```

**Expected response**:
```json
{
  "detail": "Not authenticated"
}
```

### Test Token Refresh

```bash
# Refresh tokens
curl -b /tmp/cookies.txt -c /tmp/cookies-new.txt \
  -X POST http://localhost:8000/auth/refresh
```

**Expected response**:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Test Logout

```bash
# Logout and clear cookies
curl -b /tmp/cookies.txt -c /tmp/cookies-logout.txt \
  -X POST http://localhost:8000/auth/logout
```

**Expected**: Cookies cleared, logout successful

---

## Troubleshooting

### Issue: No cookies appear after login

**Possible causes**:
1. Backend not running
2. CORS misconfiguration
3. Frontend not sending `credentials: 'include'`

**How to debug**:
```bash
# Check backend logs
cd /home/thomas/kyros-praxis/apps/api
../../.venv/bin/uvicorn app.main:app --reload --port 8000

# Check Network tab in DevTools
# Look for login request
# Check Response Headers for "Set-Cookie"
```

**Solution**:
- Verify backend is running on port 8000
- Check CORS_ALLOW_ORIGINS includes `http://localhost:3000`
- Verify login request includes `credentials: include`

---

### Issue: "Not authenticated" errors

**Possible causes**:
1. Cookies not being sent
2. Token expired
3. JWT secret mismatch

**How to debug**:
```bash
# Check if cookies exist in browser
# DevTools → Application → Cookies

# Check backend logs for errors
# Look for JWT validation errors
```

**Solution**:
- Clear all cookies and log in again
- Check backend logs for specific error
- Verify JWT_SECRET_KEY in backend .env

---

### Issue: Login works but can't access other pages

**Possible causes**:
1. Frontend routing issue
2. Auth context not providing user
3. Protected routes not checking auth

**How to debug**:
- Check browser console for errors
- Verify auth context state in React DevTools
- Check if user object is populated

**Solution**:
- Verify auth-context.tsx is wrapping your app
- Check protected route implementation
- Ensure components use `useAuth()` hook

---

### Issue: Auto-refresh not happening

**Possible causes**:
1. Interval not running
2. Refresh endpoint failing
3. Token expired before refresh

**How to debug**:
```javascript
// Check in browser console
setInterval(() => console.log('Checking auth...'), 60000);
```

**Solution**:
- Check auth context refresh interval (should be 10 min)
- Verify `/auth/refresh` endpoint works
- Check refresh token hasn't expired

---

## Security Validation Checklist

After testing, verify these security features:

### ✅ HttpOnly Cookies
- [ ] Cannot access tokens via `document.cookie`
- [ ] Cookies show HttpOnly flag in DevTools
- [ ] JavaScript cannot read/modify tokens

### ✅ Short Token Lifetime
- [ ] Access token expires in 15 minutes
- [ ] Refresh token expires in 7 days
- [ ] Old tokens don't work after expiry

### ✅ Token Rotation
- [ ] Refresh creates new tokens
- [ ] Old refresh token invalidated
- [ ] New cookies set on refresh

### ✅ CSRF Protection
- [ ] Cookies have SameSite=Lax
- [ ] Cross-origin requests blocked (if applicable)

### ✅ Proper Logout
- [ ] Logout clears all cookies
- [ ] Cannot access protected pages after logout
- [ ] Must login again

### ✅ Unauthorized Access
- [ ] Unauthenticated users redirected to login
- [ ] Protected endpoints return 401
- [ ] No data leakage to unauthenticated users

---

## Performance Testing

### Token Operations Timing

Use browser DevTools → Network tab to measure:

| Operation | Target | Typical |
|-----------|--------|---------|
| Login | < 200ms | ~125ms |
| Auth check | < 20ms | ~8ms |
| Refresh | < 200ms | ~130ms |
| Logout | < 100ms | ~45ms |

---

## Next Steps After Testing

### If Everything Works ✅

1. Test on different browsers (Chrome, Firefox, Safari)
2. Test on mobile devices (responsive design)
3. Test with slow network (DevTools → Network → Throttling)
4. Prepare for production deployment

### If Issues Found ❌

1. Check AUDIT-REPORT.md for common issues
2. Review troubleshooting section above
3. Check backend logs for errors
4. Verify configuration in .env file

---

## Production Testing Checklist

Before deploying to production:

- [ ] Change CORS_ALLOW_ORIGINS to production domain
- [ ] Set COOKIE_SECURE=true in production
- [ ] Use HTTPS (required for secure cookies)
- [ ] Test with production domain
- [ ] Verify OAuth endpoints (when needed)
- [ ] Set up monitoring/alerting
- [ ] Test account lockout (if implemented)
- [ ] Test rate limiting (if implemented)
- [ ] Security audit (external if possible)

---

## Additional Resources

- **JWT Guide**: `JWT-IMPROVEMENTS-COMPLETE.md`
- **OAuth Guide**: `OAUTH-READY-COMPLETE.md`
- **Deployment**: `DEPLOYMENT-GUIDE.md`
- **Audit Report**: `AUDIT-REPORT.md`

---

**Happy Testing!** 🧪

If you encounter any issues, check the troubleshooting section or review the comprehensive documentation in the `apps/` directory.
