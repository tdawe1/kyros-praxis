# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

Kyros is a manifest-driven monorepo with declarative architecture featuring:

- **Manifest-driven scaffolding**: `manifest.yaml` defines services, contracts, and dependencies
- **Multi-service architecture**: Console (Next.js), Orchestrator (FastAPI), Terminal-daemon (Node.js + node-pty)
- **Shared packages**: Core libraries in `packages/` for cross-service functionality
- **Contract-first development**: OpenAPI specs and Protocol Buffers for service communication
- **Docker containerization**: Services deployable via Docker Compose

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