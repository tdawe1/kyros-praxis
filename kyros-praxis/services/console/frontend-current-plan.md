# Frontend Current Plan

## Completed

- [x] Add missing dependencies: @tanstack/react-query, Tailwind CSS (with postcss, autoprefixer)
- [x] Add 7 missing pages: Create app/agents/page.tsx, app/tasks/page.tsx, app/leases/page.tsx, app/events/page.tsx, app/jobs/page.tsx, app/studio/page.tsx, app/scheduler/page.tsx, app/settings/page.tsx; use Carbon components, TanStack Query for data, data-testid
- [x] Wire pages to backend APIs: Use generated clients for /jobs, /collab/\*, add auth headers with JWT
- [x] Add unit tests: Create **tests** for components/pages (e.g., agents.test.tsx exists, expand; add for new pages)
- [x] Add E2E tests: Expand Playwright tests for happy paths (login, navigate pages, interactions)
- [x] Enhance security: Update next.config.js CSP for localhost dev (add script-src, connect-src for WS/SSE)

## Pending

- [ ] Setup Tailwind: Create tailwind.config.js (exists, but enhance), add to globals.css or similar
- [ ] Implement TanStack Query provider: Wrap app in QueryClientProvider in layout.tsx or providers
- [ ] Replace OIDC/Next-Auth with direct JWT auth: Remove Next-Auth, add JWT decoding in middleware or hooks, update auth.ts
- [ ] Fix WS integration: Enhance src/lib/ws.ts for real-time updates (e.g., SSE/WebSocket to backend at 8000)
- [ ] Update docs: Enhance services/console/README.md with setup, new features, testing instructions

## Deviations

- Using Carbon UI components for styling where possible, keeping Carbon + Tailwind integration for the UI.
