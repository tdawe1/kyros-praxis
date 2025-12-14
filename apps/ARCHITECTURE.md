# Kyros Praxis - CrewAI Stack

This directory contains the **new CrewAI-ready architecture** for Kyros Praxis, designed to replace the legacy orchestrator with a prompt-driven development workflow.

## Architecture Overview

```
┌─────────────────┐
│  console   │  Next.js 14 console for launching CrewAI runs
│  (port 3000)    │  and monitoring real-time progress via SSE
└────────┬────────┘
         │ HTTP + SSE
         ↓
┌─────────────────┐
│   api      │  FastAPI service with CrewAI integration
│   (port 8001)   │  Manifest-based agent orchestration
└────────┬────────┘
         │ SQL
         ↓
┌─────────────────┐
│   PostgreSQL    │  Stores crew_runs, crew_events
│   (port 5432)   │  Tracks execution state and results
└─────────────────┘
```

## Services

### Console (`console`)
- **Framework**: Next.js 14 with App Router
- **Purpose**: Web UI for creating crew runs, canceling jobs, and viewing live event streams
- **Port**: 3000 (default)
- **API Target**: `http://localhost:8001` (configurable via `NEXT_PUBLIC_API_BASE_URL`)

**Quick Start**:
```bash
cd console
npm install
npm run dev
# Open http://localhost:3000
```

### API (`api`)
- **Framework**: FastAPI with async support
- **Purpose**: CrewAI orchestration engine with manifest-driven workflows
- **Port**: 8001 (to avoid conflict with legacy orchestrator on 8000)
- **Database**: PostgreSQL (default: `kyros:kyros@localhost:5432/kyros`)

**Key Features**:
- **Manifest System**: YAML crew definitions in `ai/crews/` (e.g., `spec_to_tasks.yaml`)
- **Prompt Templates**: Markdown prompts in `ai/prompts/` with env var substitution
- **Provider Support**: OpenRouter (recommended) and OpenAI with automatic env mapping
- **Event Streaming**: Server-Sent Events (SSE) for real-time progress updates
- **Status Management**: Tracks runs through queued → running → succeeded/failed/canceled

**Quick Start**:
```bash
cd api
python -m venv .venv && source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Start database
docker compose up -d db

# Apply migrations
alembic upgrade head

# Set environment variables (copy from .env.example if available)
export OPENROUTER_API_KEY="your-key-here"
export MODEL_PROVIDER="openrouter"
export MODEL_NAME="openrouter/openai/gpt-4o-mini"

# Start API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

## Key Endpoints

- `POST /crews/runs` — Create a new crew run from manifest + input
- `GET /crews/runs/{id}` — Get run status and result
- `POST /crews/runs/{id}/cancel` — Cancel a running job
- `GET /crews/runs/{id}/events` — Stream Server-Sent Events (SSE) for live updates
- `GET /health` — Health check

## Crew Manifests

Crew definitions live in `api/ai/crews/*.yaml`:

```yaml
name: spec_to_tasks
description: Convert a plan/spec document into structured tasks
model:
  provider: ${MODEL_PROVIDER:-openrouter}
  name: ${MODEL_NAME:-openrouter/openai/gpt-4o-mini}
inputs:
  - name: prompt
    required: false
roles:
  - name: planner
    goal: extract actionable tasks from the plan
    prompt: spec_to_tasks.md  # References ai/prompts/spec_to_tasks.md
```

## Environment Variables

### API (`api`)
```bash
# Provider Configuration (choose one)
OPENROUTER_API_KEY=sk-or-...              # Recommended: supports multiple models
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENAI_API_KEY=sk-...                     # Direct OpenAI access

MODEL_PROVIDER=openrouter                  # openrouter | openai
MODEL_NAME=gpt-4o-mini                     # Model identifier

# Database
DATABASE_URL=postgresql+asyncpg://kyros:kyros@localhost:5432/kyros

# CORS (for console)
CORS_ALLOW_ORIGINS=["http://localhost:3000"]

# Runtime
KYROS_ENV=dev                              # dev | staging | production
KYROS_STORAGE_DIR=./storage                # Future: artifact storage
```

### Console (`console`)
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001  # CrewAI API endpoint
```

## Database Schema

The API uses PostgreSQL with two main tables:

- **crew_runs**: Stores run metadata (id, crew_id, status, input, result)
- **crew_events**: Stores event stream messages (run_id, type, payload, timestamp)

Migrations are managed with Alembic:
```bash
cd api
alembic upgrade head    # Apply migrations
alembic revision --autogenerate -m "description"  # Create new migration
```

## Testing

### API Tests
```bash
cd api
# Ensure test database is running
export TEST_DATABASE_URL=postgresql+asyncpg://kyros:kyros@localhost:5432/kyros_test
pytest
```

### Console Tests
```bash
cd console
npm test  # (when configured)
```

## Migration from Legacy Orchestrator

**Status**: The legacy orchestrator (`kyros-praxis/services/orchestrator`) is in maintenance mode. New development should target the CrewAI API.

**Key Differences**:
| Feature | Legacy (port 8000) | CrewAI API (port 8001) |
|---------|-------------------|----------------------|
| **Agent Framework** | None | CrewAI |
| **Models** | Job, Task, Event, User | CrewRun, CrewEvent |
| **Manifests** | No | YAML + Markdown |
| **Auth** | JWT + RBAC | TBD (migration planned) |
| **Real-time** | WebSocket | SSE |

**Migration Path**:
1. **Phase 1 (Current)**: Both services coexist on different ports
2. **Phase 2 (Planned)**: Port JWT auth to new API
3. **Phase 3 (Future)**: Deprecate legacy orchestrator

## Development Workflow

1. **Define Crew**: Create YAML manifest in `ai/crews/` and prompt in `ai/prompts/`
2. **Test Locally**: Use console UI or curl to trigger runs
3. **Monitor Events**: Watch SSE stream for agent progress
4. **Inspect Results**: Check run status and result JSON

Example curl flow:
```bash
# Create run
RUN_ID=$(curl -s -X POST http://localhost:8001/crews/runs \
  -H "Content-Type: application/json" \
  -d '{"crew_id":"spec_to_tasks","input":{"prompt":"Build a login system"}}' \
  | jq -r '.id')

# Stream events
curl -N http://localhost:8001/crews/runs/$RUN_ID/events

# Check result
curl http://localhost:8001/crews/runs/$RUN_ID | jq '.result'
```

## Troubleshooting

### Port Conflicts
- **Legacy orchestrator** uses port 8000
- **New CrewAI API** uses port 8001
- Run only one at a time or ensure both configs are updated

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker compose -f api/docker-compose.yml ps

# Restart database
docker compose -f api/docker-compose.yml restart db

# Check migrations
cd api && alembic current
```

### CrewAI Not Installed
```bash
pip install crewai  # Required for actual agent execution
# Without it, the API falls back to simulation mode
```

## Contributing

When adding new crew workflows:
1. Create manifest YAML in `ai/crews/`
2. Write prompt template in `ai/prompts/`
3. Update this README with example usage
4. Add tests in `api/tests/`

## Related Documentation

- [API README](./api/README.md) - Detailed API documentation
- [Console README](./console/README.md) - Console-specific setup
- [Legacy Orchestrator](../kyros-praxis/services/orchestrator/README.md) - Old system docs
- [Repository Guidelines](../AGENTS.md) - Overall project conventions
