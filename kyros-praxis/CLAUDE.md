# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

Kyros Praxis is an AI orchestration platform with a multi-service architecture featuring:

- **Multi-service architecture**: Console (Next.js), Orchestrator (FastAPI), Terminal-daemon (Node.js + node-pty)
- **Shared packages**: Core libraries in `packages/` for cross-service functionality
- **Service discovery**: Centralized service registry with health monitoring
- **AI coordination**: Zen MCP Server for multi-model AI orchestration
- **Docker containerization**: Services deployable via Docker Compose with health checks

### Directory Structure
```
services/
├── console/              # Next.js frontend (React, TypeScript, Carbon Design)
├── orchestrator/         # FastAPI backend (Python, SQLAlchemy, Redis)
└── terminal-daemon/      # WebSocket terminal service (Node.js, node-pty)

packages/                 # Shared libraries
├── core/                # TypeScript core utilities, DI container
├── agent-sdk/           # Agent development kit
├── service-registry/    # Service discovery and registration
└── [other packages]/    # Auth, eventstore, projections, etc.

scripts/                 # Automation and MCP server management
docs/                    # Architecture documentation and ADRs
```

## Development Commands

### Environment Setup
- `docker-compose up` - Start core infrastructure (Postgres, Redis)
- `docker-compose -f docker-compose.integrations.yml up <service>` - Start integration services

### Console Service (Next.js)
- `cd services/console && npm run dev` - Development server (port 3000)
- `cd services/console && npm run build` - Production build
- `cd services/console && npm run lint` - ESLint validation
- `cd services/console && npm test` - Jest test suite

### Orchestrator Service (FastAPI)
- `cd services/orchestrator && python -m uvicorn main:app --reload --port 8000` - Development server
- `cd services/orchestrator && python -m pytest` - Run test suite
- `cd services/orchestrator && alembic upgrade head` - Apply database migrations

### Terminal Daemon Service (Node.js)
- `cd services/terminal-daemon && npm run dev` - Development server with ts-node
- `cd services/terminal-daemon && npm run build` - TypeScript compilation
- `cd services/terminal-daemon && npm start` - Production server

### Scaffolding & Manifest
- `npm run scaffold:init` - Initialize new components from manifest
- `npm run scaffold:generate` - Generate code from contracts
- `npm run scaffold:validate` - Validate manifest and dependencies

### MCP (Model Context Protocol) Servers
- `./scripts/mcp-run.sh <service_name>` - Run MCP server interactively
- `./scripts/mcp-up.sh` - Start all configured MCP services

## Key Technologies & Patterns

### Frontend Stack
- **Next.js 14** with App Router
- **Carbon Design System** (IBM) for UI components
- **TanStack Query** for server state management
- **Zustand** for client state management
- **Zod** for schema validation and TypeScript integration

### Backend Stack
- **FastAPI** with async/await patterns
- **SQLAlchemy** with async PostgreSQL driver
- **Alembic** for database migrations
- **Redis** for caching and session management
- **JWT** authentication with OAuth2 flows

### Development Patterns
- **Contract-first**: API contracts defined before implementation
- **Event-driven architecture**: Event sourcing with projections
- **Dependency injection**: InversifyJS for service composition
- **Type safety**: Full TypeScript coverage with shared type definitions

## Environment Configuration

### Required Environment Variables
```bash
# Database (NO DEFAULT VALUES - must be set)
DATABASE_URL=postgresql://user:secure_password@localhost:5432/kyros
POSTGRES_DB=kyros
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# Redis
REDIS_URL=redis://localhost:6379

# Authentication (NO DEFAULT VALUES - must be set)
JWT_SECRET=your_very_secure_jwt_secret_minimum_32_chars
NEXTAUTH_SECRET=your_very_secure_nextauth_secret_minimum_32_chars
SECRET_KEY=your_very_secure_app_secret_minimum_32_chars
CSRF_SECRET=your_very_secure_csrf_secret_minimum_32_chars

# AI Services (provide at least one)
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
XAI_API_KEY=your_xai_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

### Security Configuration Rules
1. **Never use default secrets** - All environment variables must be explicitly set
2. **Minimum secret length** - 32 characters for all cryptographic secrets
3. **Rotate secrets regularly** - Implement secret rotation in production
4. **Use secure random generation** - Generate secrets with `openssl rand -hex 32`

NEXTAUTH_URL=http://localhost:3000
```

### Service Ports
- Console: `3000`
- Orchestrator: `8000`
- Terminal Daemon: `8787` (WebSocket)
- PostgreSQL: `5432`
- Redis: `6379`

## Testing Strategy

### Console (Frontend)
- **Jest** for unit tests with jsdom environment
- **Testing Library** for component testing
- **Playwright** for E2E testing
- Run: `npm test` (unit), `npm run test:e2e` (E2E)

### Orchestrator (Backend)
- **Pytest** with async test support
- **Httpx** for async HTTP client testing
- **SQLite in-memory** for test isolation
- Run: `pytest` or `python -m pytest`

### Integration Tests
- Use `docker-compose.yml` for full stack testing
- Contract testing between services via OpenAPI validation
- Event replay testing for event sourcing scenarios