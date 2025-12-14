# Frontend ↔ Backend Integration Guide

This guide explains how to connect the Kyros console to Agent A’s backend (API contract v1.0) and manually verify the full workflow.

---

## 1. Configure the API base URL

Create an `.env.local` file in `apps/console/` with your backend host:

```bash
cd apps/console
cp .env.local.example .env.local
```

Edit `.env.local`:
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
```

Tip: To avoid CORS entirely in dev, you can proxy through Next.js by setting:
```env
NEXT_PUBLIC_API_BASE_URL=/api
```
The console will send requests to `/api/*` and Next will rewrite them to the backend.

Restart `npm run dev` after changing the file so Next.js picks up the environment variable.

---

## 2. Start backend + frontend

```bash
# backend (Agent A)
cd apps/api
uvicorn app.main:app --reload --port 8001

# frontend (Console)
cd apps/console
npm install
npm run dev
```

Open http://localhost:3000 and log in (cookie-based auth).

---

## 3. Create or select a project

1. Navigate to **Planner** (or **Prompt Builder** – both route to the same workspace).
2. Use the **Project** panel:
   - Choose an existing project from the dropdown, **or**
   - Create a new project by providing name + optional description.
3. The selected project ID automatically propagates to workflow requests.

If you need to seed a project via API instead:
```bash
curl -X POST http://localhost:8001/projects \
  -H "Content-Type: application/json" \
  --cookie "access_token=..." \
  -d '{"name":"My Demo Project","description":"Test run"}'
```

---

## 4. Run the end-to-end workflow

1. Fill in the **Purpose**, **Features**, and **Tech Stack** sections (templates available).
2. Click **Generate Specification**.
   - Status banner displays planner progress.
   - Spec review card populates once `/generate` (or fallback `/specification`) completes.
3. Approve the spec or submit refinement notes.
   - Approval triggers `/approve`; status panel switches to coder/tester updates.
   - Refinements call `/regenerate` and loop back to spec review.
4. When code generation finishes, the **Generated Code** viewer unlocks (SSE fallback polls `/status` + `/code`).
5. Use the diff panel to compare iterations when refinements occur.

---

## 5. Troubleshooting tips

| Issue | Likely Cause | Resolution |
|-------|--------------|------------|
| *“Planner did not return a specification”* | `/generate` responded without `specification` | Backend still processing; the UI will auto-fetch `/projects/{id}/specification`. Re-run if it remains empty. |
| *“Unable to load projects”* | Auth cookies missing or backend offline | Re-authenticate, ensure API Base URL is correct, confirm backend running on port 8001. |
| Status panel stuck on “generating” | Workflow still running or status poll blocked | Check browser console/network for 401/500. Correlation IDs appear in the banner for quick log filtering. |
| Code viewer empty after completion | Backend returned `total_files=0` | Confirm project has generated code with `GET /projects/{id}/code`. |

---

## 6. Useful commands

```bash
# Fetch current specification for a project
curl http://localhost:8001/projects/<project_id>/specification \
  --cookie "access_token=..."

# Fetch generated code bundle
curl http://localhost:8001/projects/<project_id>/code \
  --cookie "access_token=..."
```

---

## 7. Next ideas

- Wire SSE once the backend exposes streaming events (replace polling).
- Persist project selection per user (localStorage or backend preference).
- Add Vitest coverage for the project list/create behaviours using mocked api-client functions.

---

Happy shipping! If anything breaks, capture the correlation ID from the status banner and ping Agent A with it. 🚀
