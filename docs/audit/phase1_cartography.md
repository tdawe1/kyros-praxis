# Architecture Audit Phase 1: Code Cartography

**Date**: 2025-09-13  
**Auditor**: Agent Mode  
**Repository**: kyros-praxis

## Executive Summary

This document provides a comprehensive architectural map of the Kyros Praxis monorepo, including dependency graphs, service relationships, and critical user journey flows.

## Repository Structure

```mermaid
graph TD
    A[kyros-praxis Monorepo] --> B[services/]
    A --> C[packages/]
    A --> D[agents/]
    A --> E[scripts/]
    A --> F[docs/]
    
    B --> G[orchestrator/]
    B --> H[console/]
    B --> I[terminal-daemon/]
    
    C --> J[core/]
    C --> K[agent-sdk/]
    C --> L[service-registry/]
    
    G --> M[FastAPI Backend]
    H --> N[Next.js Frontend]
    I --> O[WebSocket Terminal]
```

## Service Architecture

### Microservices Overview

| Service | Technology | Port | Purpose |
|---------|------------|------|---------|
| Orchestrator | FastAPI/Python | 8000 | REST API, auth, business logic |
| Console | Next.js/React | 3000/3001 | Web UI, user dashboard |
| Terminal Daemon | Node.js | 8080 | WebSocket terminal emulation |
| PostgreSQL | PostgreSQL 15 | 5432 | Primary database |
| Redis | Redis 7 | 6379 | Cache & session store |

### Data Flow Architecture

```mermaid
sequenceDiagram
    participant U as User
    participant C as Console (Next.js)
    participant O as Orchestrator (FastAPI)
    participant DB as PostgreSQL
    participant R as Redis
    
    U->>C: Access Dashboard
    C->>O: API Request (JWT)
    O->>R: Check Session
    O->>DB: Query Data
    DB-->>O: Return Results
    O-->>C: JSON Response
    C-->>U: Render UI
```

## Critical User Journeys

### 1. User Login Flow

```mermaid
graph LR
    A[Login Page] --> B{Credentials Valid?}
    B -->|Yes| C[Generate JWT]
    B -->|No| D[Show Error]
    C --> E[Store in Session]
    E --> F[Redirect to Dashboard]
    D --> A
```

**Components Involved**:
- Frontend: `/app/auth/login/page.tsx`
- Backend: `/services/orchestrator/auth.py`
- Database: `users` table
- Security: JWT with HS256, bcrypt password hashing

### 2. Content Scheduling Flow

```mermaid
graph TB
    A[Create Content] --> B[Select Channels]
    B --> C[Set Schedule]
    C --> D[Save to DB]
    D --> E[Queue in Celery]
    E --> F[Process at Scheduled Time]
    F --> G[Publish to Channels]
    G --> H[Update Status]
```

**Components Involved**:
- Frontend: `/app/(dashboard)/content/` 
- Backend: `/services/orchestrator/routers/tasks.py`
- Queue: Celery with Redis broker
- Database: `tasks`, `events` tables

## Dependency Analysis

### Python Dependencies (Orchestrator)
- **Core**: FastAPI, SQLAlchemy, Pydantic
- **Auth**: passlib, python-jose, python-multipart
- **Database**: alembic, asyncpg, psycopg2
- **Testing**: pytest, httpx, respx

### JavaScript Dependencies (Console)
- **Core**: React 18, Next.js 14
- **UI**: Carbon Design System
- **State**: Zustand, TanStack Query
- **Auth**: NextAuth.js
- **Testing**: Jest, Playwright

## Inter-Service Communication

```mermaid
graph LR
    A[Console] -->|REST API| B[Orchestrator]
    B -->|SQL| C[PostgreSQL]
    B -->|Cache| D[Redis]
    A -->|WebSocket| E[Terminal Daemon]
    B -->|Queue| F[Celery Workers]
```

## Configuration Management

### Environment Variables
- **Database**: `DATABASE_URL`, `POSTGRES_*`
- **Auth**: `JWT_SECRET`, `NEXTAUTH_SECRET`
- **Services**: `BACKEND_CORS_ORIGINS`, `FRONTEND_HOST`
- **Redis**: `REDIS_URL`

### Configuration Files
- Docker: `docker-compose.yml`, `docker-compose.production.yml`
- Python: `pyproject.toml`, `requirements.txt`
- JavaScript: `package.json`, `tsconfig.json`
- CI/CD: `.github/workflows/*.yml`

## Security Boundaries

```mermaid
graph TB
    subgraph Public
        A[Browser]
    end
    
    subgraph DMZ
        B[Next.js Console]
        C[WebSocket Terminal]
    end
    
    subgraph Private
        D[FastAPI Orchestrator]
        E[PostgreSQL]
        F[Redis]
    end
    
    A -->|HTTPS| B
    A -->|WSS| C
    B -->|Internal| D
    C -->|Internal| D
    D -->|Internal| E
    D -->|Internal| F
```

## Deployment Architecture

### Development
- Local Docker Compose
- SQLite for testing
- Hot reload enabled

### Production
- Docker containers
- PostgreSQL cluster
- Redis sentinel
- Nginx reverse proxy
- SSL/TLS termination

## Key Architectural Patterns

1. **Manifest-Driven Scaffolding**: Services defined in `manifest.yaml`
2. **Repository Pattern**: Database abstraction in orchestrator
3. **Dependency Injection**: FastAPI dependencies for auth/DB
4. **Event Sourcing**: Events logged to `events` table
5. **Token-Based Auth**: JWT for stateless authentication
6. **Async Operations**: Celery for background tasks

## Technical Debt Identified

- 10 TODO items across codebase (tracked in `docs/todo-burn-down.md`)
- No comprehensive E2E test suite
- Missing API documentation (OpenAPI/Swagger)
- Incomplete error handling in some endpoints
- No rate limiting implementation

## Recommendations

1. **Immediate**: Complete unit test coverage
2. **Short-term**: Implement rate limiting and API documentation
3. **Long-term**: Consider GraphQL for complex queries
4. **Strategic**: Evaluate Kubernetes for container orchestration

## Appendices

### A. File Structure Stats
- Total Files: ~500
- Lines of Code: ~25,000
- Test Coverage: ~60% (estimated)

### B. Database Schema
- Tables: 5 (users, tasks, jobs, events, alembic_version)
- Indexes: 8
- Foreign Keys: 3

### C. API Endpoints
- Public: 5 endpoints
- Authenticated: 15 endpoints
- Admin: 3 endpoints

---

*This document is part of a comprehensive architecture audit. See Phase 2 and Phase 3 for security analysis and refactoring roadmap.*