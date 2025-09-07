# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Starting the Development Environment
- `./run-dev.sh` - Starts all services (orchestrator, terminal daemon, console) with log tailing
- Individual services run on:
  - Console: http://localhost:3001 (or PORT env var)
  - Orchestrator: http://localhost:8080 (internal FastAPI service)
  - Terminal Daemon: ws://localhost:8787 (or KYROS_DAEMON_PORT env var)

### Node.js/TypeScript Commands
- `npm run dev` - Development server with hot reload (uses tsx for TypeScript)
- `npm run build` - Production build (Vite + esbuild bundle)
- `npm run start` - Run production build
- `npm run check` - TypeScript type checking
- `npm run db:push` - Push database schema changes with Drizzle

### Console App (Next.js)
- `cd apps/console && npm run dev` - Next.js dev server on port 3001
- `cd apps/console && npm run build` - Next.js production build
- `cd apps/console && npm run start` - Next.js production server

### Python/FastAPI Commands (Orchestrator)
- `cd apps/adk-orchestrator && python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload` - FastAPI dev server
- Install dependencies: `pip install --user -r apps/adk-orchestrator/requirements.txt`
- PYTHONPATH includes `packages/` and root directory for package imports

### Terminal Daemon
- `cd apps/terminal-daemon && node server.js` - WebSocket terminal daemon
- Dependencies: `cd apps/terminal-daemon && npm i`

## Architecture Overview

### Monorepo Structure
```
apps/
├── console/           # Next.js frontend (React, TypeScript)
├── adk-orchestrator/  # FastAPI backend (Python)
└── terminal-daemon/   # WebSocket terminal service (Node.js, node-pty)

packages/              # Shared Python packages
├── agent_sdk/        # Agent development kit
├── data-access/      # Database access layer
├── event_bus/        # Event messaging
├── validation/       # Validation utilities
└── [other packages]

server/               # Express.js backend (legacy/alternative?)
├── index.ts         # Main server entry
├── routes.ts        # API routes
├── storage.ts       # Storage implementations
└── vite.ts          # Vite integration
```

### Key Technologies
- **Frontend**: Next.js 15, React 18, TypeScript, Tailwind CSS, Radix UI, TanStack Query
- **Backend**: FastAPI (Python), Express.js (Node.js), SQLite/PostgreSQL with Drizzle ORM
- **Real-time**: WebSocket terminals via node-pty, planned WebSocket integration
- **Tooling**: Vite, esbuild, tsx, Drizzle Kit, UV (Python package manager)

### Database & Storage
- **ORM**: Drizzle with PostgreSQL dialect (@neondatabase/serverless)
- **Development**: In-memory storage (MemStorage) for fast iteration
- **Schema**: Runs, Agents, System Health, Users
- **Migrations**: `npm run db:push` applies schema changes

### State Management & API
- **Frontend State**: TanStack Query for server state, React Hook Form + Zod validation
- **API Design**: RESTful endpoints with structured error handling
- **Real-time Updates**: Configurable polling intervals for dashboard updates

## Development Workflow

### Prerequisites
- Node.js with npm
- Python 3.11+ with pip/uv
- Database setup (see `.env.example`)

### Environment Variables
- `NEXT_PUBLIC_ADK_URL` - Orchestrator URL (default: http://localhost:8080)
- `KYROS_DAEMON_PORT` - Terminal daemon port (default: 8787)
- `PORT` - Console app port (default: 3001)

### Package Management
- Root package.json manages shared dependencies and build tools
- Individual apps have their own package.json for specific dependencies
- Python dependencies in `apps/adk-orchestrator/requirements.txt`

### Type Safety
- Full TypeScript coverage with shared types between frontend and backend
- Zod schemas for runtime validation
- Drizzle provides type-safe database operations

## Key Patterns

### Component Architecture
- Radix UI primitives with shadcn/ui components
- Modular React components with consistent design patterns
- Component composition over inheritance

### Error Handling
- Structured error boundaries in React
- Express/FastAPI error middleware
- User-friendly error states with recovery options

### Data Flow
- Server state via TanStack Query with automatic refetching
- Form state via React Hook Form with Zod validation
- Database access through Drizzle ORM with interface-based storage pattern