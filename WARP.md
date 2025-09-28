# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Repository Overview

Kyros Praxis is an AI-powered content repurposing and scheduling platform for SMEs. This is a monorepo with multiple services and packages, using a manifest-driven architecture.

## Common Development Commands

### Initial Setup
```bash
# Install dependencies and setup environment
./scripts/setup.sh

# Quick status check of services
./scripts/quick-status.sh
```

### Backend Development (FastAPI/Python)
```bash
# Start backend server (port 8000)
cd services/orchestrator && uvicorn main:app --reload --port 8000

# Run backend tests
cd services/orchestrator && pytest

# Run specific test
pytest services/orchestrator/tests/unit/test_file.py::test_name -v

# Apply database migrations
cd services/orchestrator && alembic upgrade head

# Generate new migration
cd services/orchestrator && alembic revision --autogenerate -m "description"

# Lint Python code
ruff check  # Add --fix to auto-fix issues
```

### Frontend Development (Next.js/React)
```bash
# Start frontend server (port 3000/3001)
./scripts/start-frontend.sh
# OR
cd kyros-praxis/services/console && npm run dev

# Run frontend tests
cd kyros-praxis/services/console && npm test

# Run E2E tests
cd kyros-praxis/services/console && npx playwright test

# Build production frontend
cd kyros-praxis/services/console && npm run build

# Lint frontend code
cd kyros-praxis/services/console && npm run lint
```

### Docker & Infrastructure
```bash
# Start all services via Docker Compose
docker-compose up -d

# Start specific services
docker-compose up -d kyros-praxis-postgres kyros-praxis-redis

# Run migrations via Docker
docker-compose --profile migrate up kyros-praxis-prestart

# View logs
docker-compose logs -f [service-name]
```

### Testing & Quality Gates
```bash
# Run all tests (frontend + backend)
./bin/test-all.sh

# Run PR gate checks
python3 scripts/pr_gate.py --run-tests

# Build all services
./bin/build-all.sh
```

### Agent & MCP Management
```bash
# Start MCP servers
./scripts/start-mcp-servers.sh

# Stop MCP servers  
./scripts/stop-mcp-servers.sh

# Agent monitoring
./scripts/agent-monitor.sh

# Zen commands for task management
./scripts/zen-commands.sh
```

## Architecture Overview

### Monorepo Structure
```
/home/thomas/kyros-praxis/
├── services/           # Microservices
│   ├── console/        # Next.js frontend (React, TypeScript, Carbon Design)
│   ├── orchestrator/   # FastAPI backend (Python, SQLAlchemy, Redis)
│   └── terminal-daemon/# WebSocket terminal service (Node.js, node-pty)
├── packages/           # Shared libraries
│   ├── core/          # TypeScript core utilities, DI container
│   ├── agent-sdk/     # Agent development kit
│   └── service-registry/# Service discovery
├── kyros-praxis/      # Nested project structure with additional configs
├── agents/            # Agent configurations and prompts
├── scripts/           # Automation and development scripts
└── docs/             # Architecture documentation and ADRs
```

### Service Architecture

**Frontend (Console):**
- **Tech Stack**: Next.js 14, React 18, TypeScript, Carbon Design System, TanStack Query, Zustand
- **Port**: 3000 (container: 3001)
- **Key Dependencies**: Zod for validation, xterm for terminal UI

**Backend (Orchestrator):**
- **Tech Stack**: FastAPI, SQLAlchemy 2.x, Alembic, Pydantic, Celery, Redis
- **Port**: 8000
- **Database**: PostgreSQL (port 5432) with SQLite fallback for development
- **Auth**: JWT-based with passlib/bcrypt

**Data Flow:**
1. Frontend → API calls to Orchestrator
2. Orchestrator → Database persistence + Redis caching
3. Background jobs via Celery workers
4. Real-time updates via SSE/WebSocket

### Key API Endpoints

- `GET /healthz` - Health check
- `POST /auth/login` - JWT authentication
- `POST /collab/tasks` - Create task (requires auth)
- `GET /collab/state/tasks` - List tasks
- `GET /api/v1/utils/health-check` - Detailed health status

### Environment Configuration

Required environment variables (see `.env.example`):
```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/kyros
POSTGRES_DB=kyros
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Redis
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET=your_jwt_secret
NEXTAUTH_SECRET=your_nextauth_secret
NEXTAUTH_URL=http://localhost:3000

# API Configuration
BACKEND_CORS_ORIGINS=http://localhost:3001
FRONTEND_HOST=http://localhost:3001
```

## Development Workflow

### Git Workflow
- **Repository**: https://github.com/tdawe1/kyros-praxis
- **Branch naming**: `agents/<task-id>-<slug>` for agent work
- **PR requirements**: All tests must pass, requires review

### Testing Strategy
- **Backend**: pytest with async support, SQLite for test isolation
- **Frontend**: Jest for unit tests, Playwright for E2E
- **Coverage**: Target ≥80% for critical paths

### Code Style
- **Python**: PEP 8, 4-space indent, snake_case, type hints required
- **TypeScript**: 2-space indent, camelCase, strict types
- **Components**: PascalCase for React components
- **Tests**: Colocate with source, named `test_*.py` or `*.test.tsx`

## Agent Collaboration

The repository includes an agent collaboration system with:
- Task management in `collaboration/state/tasks.json`
- Event logging in `collaboration/events/events.jsonl`
- Agent roles: Planner, Implementer, Critic, Integrator, Watchdog

## Troubleshooting

### Common Issues

**Port conflicts:**
- Frontend default: 3000 (container: 3001)
- Backend: 8000
- PostgreSQL: 5432
- Redis: 6379

**Database connection issues:**
```bash
# Check PostgreSQL status
docker-compose ps kyros-praxis-postgres

# Apply migrations manually
cd services/orchestrator && alembic upgrade head
```

**Test failures:**
```bash
# Run tests with verbose output
pytest -v

# Check specific test isolation
pytest services/orchestrator/tests/unit -k "test_name"
```

## Important Notes

- The repository has a nested structure with `kyros-praxis/` subdirectory containing additional project files
- Multiple agent systems are configured (Codex, Gemini, Claude) with configurations in respective `.{agent}/` directories
- The project uses manifest-driven scaffolding with `manifest.yaml` defining services and dependencies
- Security: Never commit secrets, use environment variables, implement rate limiting and input validation

<citations>
  <document>
      <document_type>WARP_DOCUMENTATION</document_type>
      <document_id>getting-started/quickstart-guide/coding-in-warp</document_id>
  </document>
</citations>