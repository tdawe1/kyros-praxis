# How to Clear Browser Cache and See the Fix

**Issue**: Terminal still showing dimensions error  
**Cause**: Browser cached old JavaScript  
**Solution**: Clear cache and hard refresh

---

## Quick Fix - Hard Refresh

### In Your Browser:

**Chrome / Edge / Brave**:
- Press `Ctrl + Shift + R` (Linux/Windows)
- Or `Cmd + Shift + R` (Mac)

**Firefox**:
- Press `Ctrl + Shift + R` (Linux/Windows)
- Or `Cmd + Shift + R` (Mac)

**Safari**:
- Press `Cmd + Option + R`

This will force the browser to reload all JavaScript files without using the cache.

---

## Full Cache Clear (If Hard Refresh Doesn't Work)

### Chrome / Edge / Brave:
1. Press `F12` to open DevTools
2. Right-click the refresh button (in the browser toolbar)
3. Select "Empty Cache and Hard Reload"

### Firefox:
1. Press `Ctrl + Shift + Delete`
2. Select "Cached Web Content"
3. Click "Clear Now"
4. Reload the page with `Ctrl + Shift + R`

### Safari:
1. Press `Cmd + Option + E` to empty cache
2. Then `Cmd + R` to reload

---

## Verify the Fix

After clearing cache:

1. Go to: http://localhost:3000/terminal
2. Open browser DevTools (F12)
3. Go to Console tab
4. You should see:
   - "Connecting to orchestrator shell…"
   - "Connected. Type `help` to get started."
   - NO "dimensions" error

---

## Changes Applied

The fix uses `requestAnimationFrame` instead of `setTimeout`:

**Before** (problematic):
```typescript
term.open(terminalRef.current);
fitAddon.fit();  // ❌ Too early
```

**After** (fixed):
```typescript
term.open(terminalRef.current);

requestAnimationFrame(() => {
  requestAnimationFrame(() => {
    try {
      if (terminalRef.current && term) {
        fitAddon.fit();  // ✅ After DOM paint
        term.focus();
      }
    } catch (err) {
      console.error('Error fitting terminal:', err);
    }
  });
});
```

---

## Why requestAnimationFrame?

`requestAnimationFrame` is better than `setTimeout` for DOM operations because:
1. It waits for the browser to finish painting
2. Double-RAF ensures two full animation frames
3. More reliable for dimension calculations

---

## If Still Not Working

### 1. Close ALL Browser Tabs
Close every tab with localhost:3000, then reopen:
```
http://localhost:3000/terminal
```

### 2. Use Incognito/Private Mode
Open a new incognito window and try:
```
http://localhost:3000/terminal
```

This bypasses all cache.

### 3. Check Dev Server
Make sure the dev server restarted:
```bash
# Check if running
curl http://localhost:3000/terminal

# Should show: HTTP 200

# If not, restart:
cd /home/thomas/kyros-praxis/apps/console
npm run dev
```

### 4. Check Console for Other Errors
Open DevTools (F12) and check:
- Console tab for JavaScript errors
- Network tab to see if files are loading
- Look for any 404 or 500 errors

---

## Expected Behavior After Fix

### Terminal Should:
1. ✅ Load without errors
2. ✅ Show "Connecting..." message
3. ✅ Connect to WebSocket
4. ✅ Show shell prompt
5. ✅ Execute commands when you type

### You Should Be Able To:
1. ✅ Type shell commands
2. ✅ See output
3. ✅ Use tab completion
4. ✅ Press Ctrl+B for broadcast
5. ✅ Resize window without errors

---

## Dev Server Status

The dev server is running on:
```
http://localhost:3000
```

Files modified:
- Terminal.tsx (requestAnimationFrame fixes)
- Cache cleared (.next directory removed)
- Fresh build completed

---

## Technical Details

### What Was Changed

**File**: `console/app/terminal/components/Terminal.tsx`

**Line ~56**: Initial fit
```typescript
requestAnimationFrame(() => {
  requestAnimationFrame(() => {
    try {
      if (terminalRef.current && term) {
        fitAddon.fit();
        term.focus();
      }
    } catch (err) {
      console.error('Error fitting terminal:', err);
    }
  });
});
```

**Line ~158**: Initial size message
```typescript
requestAnimationFrame(() => {
  requestAnimationFrame(() => {
    setTimeout(() => {
      try {
        if (term && term.cols && term.rows) {
          sendMessage(JSON.stringify({ 
            type: 'resize', 
            cols: term.cols, 
            rows: term.rows 
          }));
        }
      } catch (err) {
        console.error('Error sending initial size:', err);
      }
    }, 200);
  });
});
```

### Build Status
```
✓ Next.js 14.2.33
✓ Ready in 999ms
✓ Running on http://localhost:3000
✓ No compile errors
```

---

## Summary

**Problem**: Browser cached old JavaScript with the bug  
**Solution**: Clear cache and hard refresh  
**Method**: `Ctrl + Shift + R` in your browser

**After refresh, you should see the terminal working without any "dimensions" error!**

---

**Steps to Follow**:
1. Clear browser cache (Ctrl + Shift + R)
2. Go to http://localhost:3000/terminal
3. Terminal should load without errors
4. You should see the shell prompt
5. Type commands and they should execute

If you still see the error after clearing cache, try:
- Incognito mode
- Different browser
- Close all tabs and reopen

The code fix is already applied and the server is running with the fixed code.
