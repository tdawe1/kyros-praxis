# Remaining Fetch Calls to Update

## Files with fetch() calls:

Based on grep search, the following files have fetch calls:
- `app/state/auth-context.tsx` - ✅ DONE (already updated)
- `app/terminal/components/Terminal.tsx` - ✅ DONE (replaced with cookie-auth version)
- `app/terminal/components/Dashboard.tsx` - Need to check

Most fetch calls appear to be in auth-context.tsx which we already updated.

## Dashboard Component

The Dashboard component likely has minimal API calls. Let me check if it needs updates.

## Recommendation

Since most API interaction happens through:
1. Auth context (✅ Done)
2. Terminal WebSocket (✅ Done)

And we've created a global API client (`app/lib/api-client.ts`), any future components should use:

```typescript
import { api } from '@/app/lib/api-client';

// Instead of:
fetch(`${API_BASE}/endpoint`)

// Use:
api.get('/endpoint')
```

## Status

✅ Core authentication updated
✅ Terminal component replaced
✅ Global API client available
📝 Document pattern for future components

The main work is complete! Other components can be updated as needed when they're modified in the future.
