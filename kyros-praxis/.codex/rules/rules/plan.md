# Frontend Assessment and Action Plan for Kyros Console

> Note: This repository now tracks two living implementation plans — one for the frontend and one for the backend. These plans must be kept up to date after the planning stage and throughout delivery. Any PR that changes scope or milestones should update the relevant plan file accordingly.

Quick links:
- Frontend plan: `kyros-praxis/frontend-current-plan.md`
- Backend plan: `kyros-praxis/backend-current-plan.md`

## Frontend Assessment

### Code Structure
The frontend is implemented using Next.js 14.2.5 with the App Router enabled, structured around the `app/` directory for pages and API routes, `src/lib/` for utility functions (e.g., auth.ts for Next-Auth config with OIDC provider, ws.ts for WebSocket hooks, env.ts for environment handling), `generated/` for OpenAPI-generated client code, and `contracts/` for OpenAPI spec files (api-client.yaml, auth.yaml). There are no dedicated `components/` or `hooks/` folders yet, suggesting early-stage development. The build uses Sass for styling, with paths configured in tsconfig.json for aliases like "@/lib/*" pointing to src/lib. No explicit components or hooks folders are populated beyond lib, indicating a flat, minimal structure focused on core app functionality rather than modular components.

### Key Features Implemented
- **Dashboard (app/page.tsx)**: Basic home page using Carbon React components (Button, Notification) displays a welcome message, mock job list from backend API, services list from localhost:9000, and WebSocket connection status to localhost:8000 and 9000. Uses TanStack Query for fetching jobs via generated API client, and a custom useWebSocket hook for real-time connections. Includes a test message sender for WS. Features loading states and error handling for queries.
- **Authentication**: Next-Auth v4 configured in src/lib/auth.ts for OIDC provider integration, with session and JWT callbacks to handle access tokens. Routes like /auth/login redirect if no session. Supports scopes for jobs and events.
- **API Integration**: Generated TypeScript clients (api.ts, auth.ts) from OpenAPI specs for backend communication, with fetches for jobs and services data.
- **WebSocket Support**: Custom hook in src/lib/ws.ts for connecting to backend services (orchestrator at 8000, registry at 9000), with sendMessage capability.
- **Testing Setup**: Dev deps include Jest, React Testing Library, Playwright for E2E, and axe-core for accessibility, with scripts for "test" (Jest) and "test:e2e" (Playwright). No actual test files visible in structure, indicating setup but no implementation.
- **Other**: Storybook configured for component development, codegen script for OpenAPI types.

### Dependencies
- **Core**: Next.js 14.2.5, React 18.3.1, Next-Auth 4.24.11, Zod for schema validation, Zustand for state management.
- **UI/Components**: Carbon Design System (@carbon/react 1.90.0, icons, themes) for components like Button and Notification.
- **API/Networking**: openapi-typescript for client generation, xterm for terminal features (add-ons for fit/search).
- **Testing**: Playwright, Jest with ts-jest and JSDOM environment, React Testing Library.
- **Dev Tools**: ESLint with Next.js config, TypeScript 5.5.3, Storybook 8.3.6.
- **Notable Absences**: No TanStack React Query in deps (but imported in page.tsx - this is an inconsistency, likely a missing dep causing runtime errors), no React Router (but needed for multi-page), no Tailwind CSS (uses Carbon themes and Sass instead).

### Potential Issues or Gaps
- **Stack Confirmation**: The project uses Next.js with the app router. Keep Next.js as the canonical FE stack. If styling needs expand beyond Carbon Sass, consider adding Tailwind under Next.js rather than changing frameworks. The dev port is 3000 (Next.js default).
- **Dependency Inconsistency**: Code imports useQuery from @tanstack/react-query, but it's not in package.json deps - this will break builds/runs. No deps for routing or advanced state, limiting scalability.
- **Limited Features**: Only a single page (dashboard) implemented; no dedicated pages for Agents, Tasks, Leases, Events, Jobs, Studio, Scheduler, or Settings as per plan. No routing setup (Next.js app dir supports file-based routing, but no additional pages/routes defined). Auth is OIDC-based but plan expects JWT directly - possible mismatch with backend.
- **Integration Gaps**: Fetches to localhost:9000 for services (not in plan's backend ports), WS connections to 8000/9000. No TanStack Query setup (e.g., provider wrapper), despite import. No global error handling, toasts, or feature flags (e.g., demoMode).
- **Testing Gaps**: Configured for Jest and Playwright, but no actual test files in the structure; readiness for integration testing is low.
- **Security/Performance**: CSP in next.config.js is strict but allows localhost connections (dev-only risk); no explicit rate limiting client-side. App uses 'use client' for interactivity, but no caching/optimization evident.
- **Other**: No components/hooks folders populated, suggesting stubbed or missing UI elements. Environment vars referenced but .env.example not detailed in read files (need to check if exists). No Tailwind, so styling is Carbon-only, deviating from plan.

### Overall Readiness for Integration
Basic structure is in place for a Next.js app, with a functional dashboard page that fetches and displays data, integrates auth (OIDC/Next-Auth), and sets up WS connections — it's runnable locally but in an early prototype stage. Readiness is low for full integration: no multi-page support, missing deps (TanStack not in deps), potential runtime errors from imports, and no tests. It can connect to a backend at 8000 for jobs data but needs backend services at 9000 for full functionality. Overall score: 40% ready — basic scaffolding exists, but major gaps in features, deps, and alignment with the planned Next.js stack require immediate attention before scaling or integrating deeply with the backend (e.g., orchestrator at 8000).

## Comprehensive Action Plan for Next Phase

Goal: Align frontend to plan, complete core pages, ensure local dev/test env, and prepare for backend integration within 1 week assuming 1 full-time developer.

### Prioritized Tasks (Logical Order)
1. **Fix Immediate Issues (Day 1)**: Update package.json to include missing deps like @tanstack/react-query, resolve import errors. Add missing .env.example entries for frontend (e.g., NEXTAUTH_* vars). Estimated time: 2-4 hours. Resources: npm. Milestone: App builds and runs without errors.
2. **Local Development Setup (Day 1)**: Create/update scripts/start-frontend.sh for cd to services/console && npm install && npm run dev (port 3000 as current). Document in services/console/README.md: clone repo, cd to console, npm i, copy .env.example to .env and fill placeholders (e.g., NEXTAUTH_URL=http://localhost:3000, API endpoints). Add initial test scenario in docs: "Run npm run dev and verify dashboard loads at http://localhost:3000, check WS connections in console." Estimated time: 4-6 hours. Resources: npm, bash scripting.
3. **Align Stack and Add Basic Structure (Days 1-2)**: Keep Next.js (app router). Install missing deps, wire TanStack Query Provider, and optionally add Tailwind for styling alongside Carbon. Establish page structure for jobs/auth/settings. Update tsconfig paths if needed. Milestone: Next.js app with routing and data layer ready.
4. **Implement Core Pages (Days 2-4)**: Add missing pages (Agents, Tasks Kanban, Leases, Events with live tail, Studio, Scheduler, Settings) using planned stack (TanStack Query for data fetching, Zustand for state). Wire to backend APIs (e.g., /jobs, /collab/*). Add data-testid attributes. Estimated time: 2 days. Resources: React dev tools. Milestone: All 8 pages navigable, displaying stub data, with auth guarded routes.
5. **Enhance Integration and Features (Days 4-5)**: Integrate TanStack Query provider, add optimistic updates for interactions (e.g., task transitions). Implement WS for real-time updates on pages like Events/Leases. Add toasts and error handling. Estimated time: 1-2 days. Resources: Backend running on 8000. Milestone: End-to-end flow for creating/viewing jobs works locally.
6. **Testing Setup (Days 5-6)**: Add unit tests for components/hooks using Jest + React Testing Library (e.g., dashboard load, auth flow). Implement Playwright E2E for initial scenarios (dashboard load, login, create job stub). Run and fix tests. Estimated time: 1 day. Milestone: good coverage on core paths, e2e tests passing.
7. **Documentation and Polish (Day 6)**: Update services/console/README.md with full setup instructions, dependency install, config (e.g., .env for API/WS endpoints), and test scenarios (e.g., "Test dashboard loads and shows jobs list from localhost:8000"). Add an ADR confirming Next.js as the frontend stack (and if Tailwind is adopted alongside Carbon). Estimated time: 4 hours.

### Estimated Timelines
- Total: 1 week (5 dev days, assuming 8-hour days).
- Breakdown: Task 1: 0.5 day; Task 2: 0.5 day; Task 3: 2 days; Task 4: 2 days; Task 5: 1 day; Task 6: 1 day; Task 7: 0.5 day.

### Required Resources
- Node.js 20+ for frontend.
- npm/yarn for dependency management.
- Backend services (orchestrator at 8000, registry at 9000) running locally for integration.
- Docker if using compose for deps (not currently, but recommended for full env).
- Dev tools: VSCode with extensions for TS/Next.js, Playwright.

### Milestones
1. **Day 1 End**: Local dev env running - install deps, start server, access dashboard without errors.
2. **Day 3 End**: Stack aligned to plan (Next.js; Tailwind optional), basic pages implemented, local env fully scripted.
3. **Day 5 End**: Full integration with WS/data fetching, tests passing for core flows.
4. **Day 6 End**: Documentation complete, ready for backend integration.

```mermaid
flowchart TD
    A[Project Start] --> B[Fix Dependencies & Config]
    B --> C[Local Setup Scripts & .env]
    C --> D[Stack Alignment: Confirm Next.js; add Tailwind (optional)]
    D --> E[Implement Core Pages & Router]
    E --> F[Add TanStack Query & WS Integration]
    F --> G[Unit & E2E Tests]
    G --> H[Documentation & Review]
    H --> I[Milestone: Frontend Ready for Integration]
```
