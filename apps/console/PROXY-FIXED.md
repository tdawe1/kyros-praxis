# Proxy Configuration Fixed

## Problem
Console was trying to connect to port **8000** instead of **8001**

## Root Cause
Next.js cache (.next folder) had stale configuration

## Solution Applied

1. **Stopped console**
2. **Cleared .next cache**: `rm -rf .next`
3. **Verified next.config.js** points to port 8001
4. **Restarted console**

## Configuration

### next.config.js
```javascript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://localhost:8001/:path*',  // ← Port 8001
    },
  ];
}
```

### .env.local
```
NEXT_PUBLIC_API_BASE_URL=/api
```

## Verification

Test these URLs:

1. **Direct API**: http://localhost:8001/health
2. **Proxied API**: http://localhost:3000/api/health
3. **Test page**: http://localhost:3000/test-api.html

All should work now!

## If Port 8000 Still Appears

### Hard Refresh Browser
- **Chrome/Edge**: Ctrl+Shift+R (Cmd+Shift+R on Mac)
- **Firefox**: Ctrl+F5
- Or open in **Incognito/Private mode**

### Clear Next.js Cache Again
```bash
cd /home/thomas/kyros-praxis/apps/console
rm -rf .next
npm run dev
```

### Check Console Logs
```bash
tail -f /tmp/console-fixed.log | grep -E "proxy|8000|8001"
```

Should only see references to 8001, not 8000.

## Current Status

✅ API running on port 8001  
✅ Console running on port 3000  
✅ Proxy configured for port 8001  
✅ Cache cleared

**Test in browser**: http://localhost:3000/test-api.html
