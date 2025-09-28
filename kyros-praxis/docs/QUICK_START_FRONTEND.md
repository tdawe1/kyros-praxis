# Quick Start — Console (Frontend)

This guide gets the Next.js console running locally and connected to the orchestrator.

Prereqs
- Node.js 18+ (or 20+)
- npm (or pnpm/yarn), curl, jq
- Orchestrator API running locally on http://localhost:8000 (see docs/QUICK_START.md)

1) Install and configure
```bash
cd services/console
npm ci
cp .env.example .env
# Edit .env (minimum):
# NEXTAUTH_URL=http://localhost:3001
# Generate a secret:
NEXTAUTH_SECRET=$(node -e "console.log(require('crypto').randomBytes(32).toString('base64'))")
echo "NEXTAUTH_SECRET=$NEXTAUTH_SECRET" >> .env
# Orchestrator base URL
# NEXT_PUBLIC_ADK_URL=http://localhost:8000
```

2) Run the dev server
```bash
npm run dev
# Open http://localhost:3001
```

3) Log in
- Seed a user in the orchestrator (see docs/QUICK_START.md, e.g., dev@example.com / password)
- Use the console’s login UI with those credentials

4) Smoke checks
- Dashboard loads without errors
- Jobs page lists jobs from /api/v1/jobs (empty initially)
- Tasks page loads and fetches /api/v1/collab/state/tasks

5) Tests
```bash
# Unit tests
npm test
# E2E tests (ensure dev server is running and orchestrator is up)
npx playwright test
```

Notes
- API base: `NEXT_PUBLIC_ADK_URL` must match your orchestrator (default http://localhost:8000)
- Auth: NextAuth v5 credentials flow posts JSON to orchestrator `/auth/login`
- Server state: TanStack Query is installed; ensure app is wrapped with a QueryClientProvider
- CSP: next.config.js allows localhost WS/SSE for dev

