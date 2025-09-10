# Kyros Console - Local Development Setup

## Setup Instructions

1. Clone the repo: `git clone <repo-url>`
2. `cd services/console`
3. `npm install`
4. Copy `.env.example` to `.env` and fill placeholders (e.g., `NEXTAUTH_URL=http://localhost:3000`, `API_BASE_URL=http://localhost:8000`, `WS_URL=ws://localhost:8000`).
5. Run `npm run dev` to start at http://localhost:3000.

## Verification

Load http://localhost:3000, check browser console for no errors, verify dashboard loads with mock jobs from localhost:8000, confirm WS connections to 8000/9000 in dev tools.