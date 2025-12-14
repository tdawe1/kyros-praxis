# Kyros Praxis Console

A Next.js front-end for the PRD multi-agent workflow. It lets you create projects, capture structured prompts, review planner specs, approve/refine iterations, and inspect generated code/test files.

## Quick Start

1. **Install dependencies**
   ```bash
   cd apps/console
   npm install
   ```

2. **Set the backend base URL**
   ```bash
   cp .env.local.example .env.local
   # edit .env.local (default uses CrewAI API on http://localhost:8001)
   # Optional: set NEXT_PUBLIC_API_BASE_URL=/api to use built-in proxy
   ```

3. **Run the backend (CrewAI API)**
   ```bash
   cd apps/api
   uvicorn app.main:app --reload --port 8001
   ```

4. **Launch the console**
   ```bash
   cd apps/console
   npm run dev
   ```

5. **Open the app**
   Visit <http://localhost:3000>, sign in (cookie-based auth), and head to **Planner** or **Prompt Builder** to start the workflow.

> Detailed integration steps (including manual curl commands) live in [`docs/INTEGRATION_GUIDE.md`](./docs/INTEGRATION_GUIDE.md).

## Key Features

- **Project selector** – list existing projects (`GET /projects`) or create a new one before planning.
- **Prompt builder** – guided sections with validation, templates, and live preview.
- **Workflow orchestration** – calls `/projects/{id}/generate`, `/approve`, `/regenerate`, and polls `/status` to mirror planner/coder/tester progress.
- **Spec review** – displays planner output with validation scores, supports refinement notes.
- **Code viewer** – hierarchical tree, syntax highlighting, copy-to-clipboard, and diff view between iterations.
- **Correlation-aware errors** – any API error surfaces the `X-Correlation-ID` for backend debugging.

## Scripts

- `npm run dev` – Start the Next.js dev server.
- `npm run build` – Build for production.
- `npm run start` – Run the production build.
- `npm run test` – Execute Vitest unit tests.
- `npm run storybook` – Launch component explorer for shared UI primitives.

## Notes

- The workspace uses cookie-based auth (`credentials: 'include'`). Ensure the backend issues `access_token` cookies on login.
- Polling is used for workflow status until SSE endpoints are available.
- Environment-specific tuning (ports, hostnames) happens via `NEXT_PUBLIC_API_BASE_URL` in `.env.local`.

Happy shipping! 🚀
