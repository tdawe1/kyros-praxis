# Development Guidelines

## Project Structure

Kyros Praxis CrewAI Stack - A prompt-driven development platform using CrewAI for agent orchestration.

```
kyros-praxis/
├── api/          - FastAPI backend with CrewAI integration
├── console/      - Next.js 14 frontend dashboard
├── daemon/       - Terminal daemon service (optional)
└── docs/         - Additional documentation
```

### Core Services

- **API** (`/api`) - FastAPI service with CrewAI integration (port 8001)
  - JWT authentication
  - Manifest-based crew orchestration
  - Real-time event streaming (SSE)
  - PostgreSQL database

- **Console** (`/console`) - Next.js 14 app for CrewAI run management (port 3000)
  - User authentication UI
  - Crew run creation and monitoring
  - Real-time event visualization

- **Database** - PostgreSQL for users, crew runs, and events

## Build, Test, and Development Commands

### Console (Frontend)
```bash
cd console
npm install
npm run dev              # Start dev server (port 3000)
npm run build            # Production build
npm run lint             # Lint code
```

### API (Backend)
```bash
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head     # Apply migrations
uvicorn app.main:app --reload --port 8001  # Start API
pytest                   # Run tests
```

### Database
```bash
cd api
docker compose up -d db  # Start PostgreSQL
docker compose down      # Stop services
```

## Coding Style & Naming Conventions

### Python (API)
- **Indentation**: 4 spaces
- **Functions**: snake_case
- **Classes**: PascalCase
- **Models**: Pydantic models in `app/models.py`, SQLAlchemy in `app/db/models.py`
- **Routers**: Place in `app/routers/`

### TypeScript/React (Console)
- **Indentation**: 2 spaces
- **Components**: PascalCase
- **Hooks**: camelCase with `use` prefix
- **Files**: PascalCase for components, camelCase for utilities
- Run `npm run lint` before commits

### General
- Environment variables in `.env`, never hardcode secrets
- Use absolute imports where possible
- Document public APIs with docstrings/JSDoc

## Testing Guidelines

### API Tests
```bash
cd api
pytest                          # Run all tests
pytest tests/test_auth.py       # Specific test file
pytest -v                       # Verbose output
```

### Console Tests
```bash
cd console
npm test                        # Run Jest tests (when configured)
npm run test:e2e               # E2E tests (when configured)
```

## Commit & Pull Request Guidelines

Follow Conventional Commits:
- `feat(api): add password reset endpoint`
- `fix(console): correct token expiration handling`
- `chore(deps): update dependencies`
- `docs: update authentication guide`

Pull requests should:
- Have clear description of changes
- Include test verification steps
- Link to related issues
- Include screenshots for UI changes

## Configuration & Security Tips

- **Never commit `.env` files** - use `.env.example` as template
- **JWT secrets**: Minimum 32 characters, generate with `openssl rand -hex 32`
- **API keys**: Store in environment variables, never in code
- **Dependencies**: Regular updates with `npm audit` / `pip list --outdated`
- **CORS**: Restrict to specific origins in production
- **HTTPS**: Required in production (use reverse proxy)
