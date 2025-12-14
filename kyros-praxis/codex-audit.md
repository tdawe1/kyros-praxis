**Phase 1: Code Cartography & De‑tangling**

- High-Level Purpose
  - Kyros Praxis is a multi-service platform for AI/agent orchestration. It provides a backend orchestrator API (FastAPI), a web console (Next.js + NextAuth), and a terminal daemon (Node.js + WebSockets) to coordinate jobs/tasks, user auth, and real-time terminal sessions.

- Tech Stack & Dependencies
  - Backend (Orchestrator): Python 3.11+, FastAPI, SQLAlchemy 2.x (sync + async), Alembic, Pydantic v2, python-jose (JWT), Passlib/Bcrypt, Redis (optional), SSE, dotenv.
    - Pinned in `kyros-praxis/services/orchestrator/requirements.txt`:
      - fastapi 0.115.0, uvicorn 0.32.0, sqlalchemy[asyncio] 2.0.35, alembic 1.16.5, pydantic 2.11.7, python-jose 3.3.0, passlib[bcrypt] 1.7.4, bcrypt 4.1.2, pyjwt 2.8.0, cryptography 41.0.7, python-dotenv 1.1.1
      - dev: pytest 8.4.2, pytest-asyncio 1.1.0, httpx 0.27.2, asgi-lifespan 2.1.0
      - rate limiting: slowapi 0.1.9, redis 5.0.8, aiosqlite 0.20.0
  - Frontend (Console): Next.js 14, React 18, NextAuth v5, React Query 5, Carbon, Zod, Zustand, jwt-decode, Tailwind.
    - Pinned in `kyros-praxis/services/console/package.json`:
      - next 14.2.5, next-auth ^5.0.0-beta.29, react 18.3.1, @tanstack/react-query 5.59.15, @carbon/react 1.90.0, zod 3.23.8, jwt-decode 4.0.0, etc.
  - Terminal Daemon: Node 18+, Express, ws, node-pty, jose, cors, helmet, express-rate-limit.
    - Pinned in `kyros-praxis/services/terminal-daemon/package.json`:
      - express ^4.19.2, ws ^8.18.0, node-pty ^1.0.0, helmet ^7.1.0, jose ^5.9.3, etc.
  - External services: Postgres, Redis, optional Qdrant (present in repo config), SSE.

- Architectural Components
  - Data Models (`kyros-praxis/services/orchestrator/models.py`)
    - User(id, email, password_hash)
    - Job(id, name, status, created_at)
    - Task(id, title, description, version, created_at)
    - Event(id, type, payload, created_at)
  - API Endpoints (FastAPI app in `main.py`, routers in `routers/`)
    - Root/health: `GET /`, `GET /health`, `GET /healthz`
    - Auth: `POST /auth/login` (returns JWT)
    - WebSocket: `WS /ws` (requires auth)
    - Jobs: `POST /api/v1/jobs`, `GET /api/v1/jobs`, `GET /api/v1/jobs/{id}`, `DELETE /api/v1/jobs/{id}` (501)
    - Tasks: `POST /api/v1/collab/tasks`, `GET /api/v1/collab/state/tasks`
    - Utils: `GET /api/v1/utils/health-check`, `GET /api/v1/utils/info`
    - Events (file-backed): `POST /events`, `GET /events/tail` (SSE)
  - Key Services/Modules
    - Auth (`auth.py`): password hashing (bcrypt), JWT creation/verification, current user extraction
    - DB (`database.py`): sync + async engines, default SQLite; supports Postgres via env
    - Security (`security_middleware.py`, `middleware.py`): CSRF, rate limiting, headers (not wired in app), API key validator, optional slowapi limiter
    - Validation (`utils/validation.py`): Pydantic validation for Job/Task inputs
  - State Management
    - Backend: database persistence; in-memory rate limiting in `SecurityMiddleware` (not applied); events file on disk
    - Frontend: React Query for server state, NextAuth session with JWT, optional persisted UI state via `localStorage`
  - Data Flow
    - User → Console (Next.js) → NextAuth sign-in → Orchestrator `/auth/login` → JWT → Console calls Orchestrator REST (`/api/v1/...`) → Orchestrator DB (SQLite/Postgres).
    - Realtime: Console WebSocket → Orchestrator `/ws` (auth required) [currently mismatched].
    - Events: `POST /events` appends JSON lines to file; `GET /events/tail` streams via SSE.

  Text flow diagram:
  User → Console UI → NextAuth (Credentials) → Orchestrator /auth/login → JWT
  → Console fetch → Orchestrator REST → DB
  → Console WS → Orchestrator /ws (should include JWT) → Real-time echo

**Phase 2: Critical Flaw Identification**

1) Title: JWT creation/verification mismatch (algorithm, claims, and missing null-guard)
- Location: File: kyros-praxis/services/orchestrator/auth.py, Lines: 19-23, 64-73, 76-103
- Severity: P0-CRITICAL
- Code Snippet:
  - Lines 22-23: ALGORITHM = "HS256"; ACCESS_TOKEN_EXPIRE_MINUTES = 30
  - Lines 71-73: encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
  - Lines 87-93: jwt.decode(..., algorithms=[ALGORITHM], audience="api", issuer="https://orchestrator.local")
  - Lines 76-79/87-93: credentials is optional but used unguarded: credentials.credentials
- Analysis:
  - Tokens created in `create_access_token` contain only sub/exp but are later decoded requiring audience/issuer; these tokens will fail validation.
  - Algorithm is hardcoded to HS256, while config elsewhere prefers HS512.
  - `oauth2_scheme = HTTPBearer(auto_error=False)` returns None when missing, then `credentials.credentials` raises AttributeError → 500 instead of 401.
- Recommendation:
  - Unify JWT config via `app.core.config.settings` (algorithm, issuer, audience, expiries).
  - Add `aud` and `iss` claims at creation and verify consistently.
  - Set `HTTPBearer(auto_error=True)` or explicitly guard `if not credentials: raise 401`.

2) Title: Security middleware not applied (no CSRF, rate limiting, or headers)
- Location: File: kyros-praxis/services/orchestrator/main.py, Lines: entire file (no setup_security call)
- Severity: P1-HIGH
- Code Snippet: N/A (absence). `security_middleware.setup_security()` exists but never used.
- Analysis:
  - None of the CSRF, rate limit, or security headers in `security_middleware.py` are active. API is missing important protections.
- Recommendation:
  - In `main.py`, instantiate config and call `setup_security(app, config)` early in startup, wiring CORS and middleware.

3) Title: Insecure CSRF token generation/validation (length check only)
- Location: File: kyros-praxis/services/orchestrator/security_middleware.py, Lines: 83-110
- Severity: P1-HIGH
- Code Snippet:
  - Line 100: return secrets.token_urlsafe(32)  # Simplified for demo
  - Line 110: return len(token) == 43
- Analysis:
  - The CSRF token is not signed/validated beyond length; an attacker can forge a valid-looking token trivially.
- Recommendation:
  - Implement signed, time-bounded tokens (HMAC of nonce+timestamp) and verify signature and age. Consider using standard anti-CSRF patterns or established libraries.

4) Title: Overly permissive CSP on API responses
- Location: File: kyros-praxis/services/orchestrator/security_middleware.py, Lines: 240-250
- Severity: P2-MEDIUM
- Code Snippet:
  - "script-src 'self' 'unsafe-inline' 'unsafe-eval'"
- Analysis:
  - Allowing inline scripts and eval in CSP significantly increases XSS risk. While comment suggests tightening in production, there is no environment gating here and middleware isn’t even applied.
- Recommendation:
  - Remove `'unsafe-inline'` and `'unsafe-eval'` for production; gate dev allowances via env and ensure middleware is applied.

5) Title: NextAuth dev-only authorize accepts any credentials; default secret fallback
- Location: File: kyros-praxis/services/console/lib/auth-v5.ts, Lines: 12-16, 20
- Severity: P0-CRITICAL
- Code Snippet:
  - Lines 12-16: returns dev user regardless of password (or with default email)
  - Line 20: secret: process.env.NEXTAUTH_SECRET || "dev-secret"
- Analysis:
  - In production, this allows anyone to authenticate; default static secret undermines token integrity.
- Recommendation:
  - Replace dev-only authorize with real verification (e.g., proxy to orchestrator /auth/login).
  - Enforce `NEXTAUTH_SECRET` presence in all environments except local dev; fail startup otherwise.

6) Title: WebSocket client lacks auth and uses ws://
- Location: File: kyros-praxis/services/console/lib/ws.ts, Lines: 17, 26-33
- Severity: P1-HIGH
- Code Snippet:
  - Line 17: default ws://localhost:8000/ws
  - No Authorization header, subprotocol, or token query param
- Analysis:
  - Backend requires `get_current_user` for `/ws` but client sends no JWT, and uses insecure ws by default. Connection will fail; if server ever allowed unauth WS, this would be insecure.
- Recommendation:
  - Pass JWT via query string or subprotocol; use `wss://` in production; derive URL from config; rotate token if expired.

7) Title: Secrets and credentials committed to repo in .env files
- Location: File: kyros-praxis/services/orchestrator/.env (multiple lines), root .env files
- Severity: P0-CRITICAL
- Code Snippet: Contains secrets (redacted), includes database creds and JWT/CSRF keys.
- Analysis:
  - Sensitive values are tracked in Git. Even if noted “for local only,” this creates leakage risk and drift (e.g., `NEXT_PUBLIC_FEATURE_MARKETING=falseSECRET_KEY=...` suggests malformed env composition).
- Recommendation:
  - Remove `.env` from VCS; commit only `.env.example`. Rotate any exposed credentials. Add pre-commit checks to prevent secret commits.

8) Title: Mixed sync/async SQLAlchemy usage with side-effectful import
- Location: Files: kyros-praxis/services/orchestrator/database.py, Lines: 1-40, 51-62; routers/tasks.py vs routers/jobs.py
- Severity: P2-MEDIUM
- Code Snippet:
  - Tables created at import (Lines ~30-36): `Base.metadata.create_all(bind=engine)` in a try/except; sync+async engines both defined; routers mix sync sessions (`get_db`) and async sessions (`get_db_session`).
- Analysis:
  - Creating tables on import is brittle; mixing sync/async increases complexity and potential deadlocks or inconsistent transaction handling.
- Recommendation:
  - Remove side effects from import; create tables via migrations (Alembic). Standardize on async or sync path across routers.

9) Title: `get_current_user` raises 500 on missing Authorization header
- Location: File: kyros-praxis/services/orchestrator/auth.py, Lines: 76-93
- Severity: P1-HIGH
- Code Snippet:
  - HTTPBearer(auto_error=False) and unguarded `credentials.credentials`
- Analysis:
  - Missing token triggers AttributeError not caught by JWTError except, causing 500 instead of 401.
- Recommendation:
  - Use `auto_error=True` or explicitly handle `if not credentials: raise 401`.

10) Title: Event API returns non-standard response and writes under repo path
- Location: File: kyros-praxis/services/orchestrator/routers/events.py, Lines: 25-59
- Severity: P2-MEDIUM
- Code Snippet:
  - Returns `({ "ok": True }, {"ETag": etag})` which FastAPI won’t interpret as desired headers; writes JSONL to a path relative to repo root.
- Analysis:
  - ETag not set properly; writing to source tree is fragile and can fail in containerized or read-only deployments.
- Recommendation:
  - Use `Response` to set headers explicitly; write to a configured data directory.

11) Title: Divergent JWT configuration between modules
- Location: Files: `auth.py` (HS256, 30m), `app/core/config.py` (HS512, 120m), `security_middleware.py` (HS256 default)
- Severity: P2-MEDIUM
- Code Snippet:
  - `auth.py` Line 22; `config.py` JWT_ALGORITHM="HS512"; `security_middleware.py` Line 30 defaults HS256.
- Analysis:
  - Inconsistent algorithms and expiries cause broken auth and accidental lockouts.
- Recommendation:
  - Centralize JWT settings (algorithm, issuer, audience, expiries) in `settings` and import consistently.

12) Title: CORS and security header gaps for API service
- Location: File: kyros-praxis/services/orchestrator/main.py (no CORS/headers), `security_middleware.py` not wired
- Severity: P1-HIGH
- Analysis:
  - Orchestrator does not set CORS/security headers; Next.js console sets good headers for itself but API lacks them.
- Recommendation:
  - Add `CORSMiddleware` with configured origins; add security headers via middleware.

**Phase 3: Strategic Refactoring Roadmap**

- Executive Summary
  - The codebase is functional but inconsistent. Authentication is currently broken and insecure due to mismatched JWT implementations, inactive security middleware, and a dev-only NextAuth flow that grants access unconditionally. CSRF protection and CSP in the API are incomplete or inactive. Configuration is duplicated and contradictory across modules. There are also maintainability issues: mixed sync/async DB access, side effects on import, and file-backed event storage under source paths. Immediate focus should be on unifying auth/security, removing secrets from VCS, and wiring middleware.

- Prioritized Action Plan
  - [P0 - CRITICAL]
    - Fix NextAuth Credentials provider: remove dev-only authorize, enforce `NEXTAUTH_SECRET` presence; integrate with orchestrator `/auth/login`.
    - Unify JWT across services: single algorithm (HS512 recommended), add `iss` and `aud` claims in token creation; verify consistently.
    - Remove secrets from repo; rotate exposed credentials; add secret scanning and pre-commit hooks.
  - [P1 - HIGH]
    - Apply security middleware in orchestrator (`setup_security(app, config)`): enable CSRF, rate limiting, security headers, and CORS.
    - Replace CSRF stub with signed, time-bounded tokens; verify signature and max age.
    - Fix `get_current_user` missing-token path to return 401 not 500.
    - Update WebSocket client to authenticate (JWT via subprotocol/query) and use `wss://` in production.
  - [P2 - MEDIUM]
    - Consolidate configuration in `app/core/config.py`; remove duplicated constants in `auth.py` and `security_middleware.py`.
    - Standardize DB access (choose async or sync); remove table-creation side effects; rely on Alembic.
    - Correct Events API response with proper header setting and move event file path to a configured data directory.
    - Tighten CSP: remove `'unsafe-inline'`/`'unsafe-eval'` in production; gate dev relaxations via env.
    - Normalize ETag behavior across endpoints; avoid quoting drift.

- Testing & Validation Strategy
  - Unit tests
    - Auth: token creation includes `iss`/`aud`, decoding validates; missing/invalid bearer returns 401.
    - CSRF: token generation + validation path, including max-age and signature verification.
    - Middleware: rate limit thresholds and reset headers.
  - Integration tests
    - NextAuth sign-in → Orchestrator `/auth/login` → protected endpoints (jobs/tasks) succeed with JWT and fail without.
    - WebSocket connect with valid token succeeds, invalid/omitted token fails.
    - CORS preflight behavior from Console origin.
  - Security checks
    - Add `pip-audit` and `npm audit` to CI; apply dependabot or renovation bot.
    - Add Bandit and ESLint security rules; enable ruff for Python (`ruff check`).
  - Operational validation
    - Alembic migration flow for clean setup (no auto-creation at import).
    - Secrets presence validation at startup; fail-fast in non-local environments.

- Documentation Blueprint
  - Security Architecture doc: JWT structure, claims, algorithms; CSRF strategy; CORS policy; WebSocket auth pattern.
  - Auth Integration guide: Console ↔ Orchestrator, NextAuth config (prod vs dev).
  - Deployment README: env vars (non-example), secret management, TLS expectations (HTTPS/WSS).
  - DB and Migrations guide: running Alembic; async vs sync approach choice.
  - Eventing spec: storage location, rotation, and SSE contract.

If you want, I can:
- Patch `auth.py` + `main.py` to adopt `settings` for JWT and wire `setup_security`.
- Replace NextAuth dev authorize with orchestrator-backed flow and enforce secrets.
- Add a secure WS auth pattern and update the console hook.
- Remove committed `.env` files and add `.env.example`, plus a secret-scanning pre-commit.

Say the word and I’ll implement the P0/P1 fixes with tests.
