# Quick Start Guide

Get the Kyros Praxis CrewAI stack running in 5 minutes!

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 16+ (or Docker)
- OpenRouter API key ([get one here](https://openrouter.ai/keys))

---

## Step 1: Database Setup

### Option A: Using Docker (Recommended)

```bash
cd apps/api
docker compose up -d db
```

### Option B: Existing PostgreSQL

Create a database:
```sql
CREATE DATABASE kyros;
CREATE USER kyros WITH PASSWORD 'kyros';
GRANT ALL PRIVILEGES ON DATABASE kyros TO kyros;
```

---

## Step 2: API Setup

```bash
cd api

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your values:
# - OPENROUTER_API_KEY=sk-or-v1-your-key-here
# - JWT_SECRET_KEY=$(openssl rand -hex 32)
# - DATABASE_URL=postgresql+asyncpg://kyros:kyros@localhost:5432/kyros

# Run database migrations
alembic upgrade head

# Start the API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

**API now running at**: http://localhost:8001

---

## Step 3: Console Setup

```bash
cd console

# Install dependencies
npm install

# Create .env (optional - defaults to localhost:8001)
echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8001" > .env.local

# Start the console
npm run dev
```

**Console now running at**: http://localhost:3000

---

## Step 4: Test the Stack

### Via Console UI

1. Open http://localhost:3000
2. (Optional) Register/Login
3. Enter a prompt: "Build a todo app"
4. Click "Start Run"
5. Watch the events stream in real-time!

### Via cURL

```bash
# Health check
curl http://localhost:8001/health

# Register user (optional)
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","email":"demo@example.com","password":"password123"}'

# Login (optional)
TOKEN=$(curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"password123"}' \
  | jq -r '.access_token')

# Create a crew run
RUN_ID=$(curl -X POST http://localhost:8001/crews/runs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"crew_id":"spec_to_tasks","input":{"prompt":"Build a login system"}}' \
  | jq -r '.id')

echo "Run ID: $RUN_ID"

# Watch events (SSE stream)
curl -N http://localhost:8001/crews/runs/$RUN_ID/events

# Get final result
curl http://localhost:8001/crews/runs/$RUN_ID | jq '.result'
```

---

## Troubleshooting

### API won't start

**Problem**: "JWT_SECRET_KEY must be set"

**Solution**: 
```bash
cd api
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env
```

---

**Problem**: "Database connection failed"

**Solution**:
```bash
# Check if PostgreSQL is running
docker compose ps  # or: systemctl status postgresql

# Verify connection
psql postgresql://kyros:kyros@localhost:5432/kyros -c "SELECT 1;"
```

---

### Console can't connect to API

**Problem**: Console shows connection errors

**Solution**: 
1. Verify API is running: `curl http://localhost:8001/health`
2. Check console .env: `cat .env.local`
3. Restart console: `npm run dev`

---

### CrewAI runs fail

**Problem**: Runs fail with "CrewAI unavailable"

**Solution**:
```bash
# Install CrewAI
cd api
source .venv/bin/activate
pip install crewai

# Verify OpenRouter key is set
grep OPENROUTER_API_KEY .env
```

---

## Next Steps

- **Frontend Team**: See [api/AUTH_API.md](api/AUTH_API.md) for auth integration
- **Backend Team**: Review [ARCHITECTURE.md](ARCHITECTURE.md) for architecture details
- **Everyone**: Check [PHASE2-AUTH-COMPLETE.md](PHASE2-AUTH-COMPLETE.md) for auth features

---

## Stack Overview

```
┌─────────────────┐
│ Browser         │  http://localhost:3000
│ (Next.js)       │
└────────┬────────┘
         │ HTTP + SSE
         ↓
┌─────────────────┐
│ API             │  http://localhost:8001
│ (FastAPI)       │  - /auth/* (registration, login)
│                 │  - /crews/runs (create, monitor)
└────────┬────────┘
         │ asyncpg
         ↓
┌─────────────────┐
│ PostgreSQL      │  localhost:5432/kyros
│                 │  - users, crew_runs, crew_events
└─────────────────┘
         │ requests
         ↓
┌─────────────────┐
│ OpenRouter      │  https://openrouter.ai/api/v1
│ (LLM Provider)  │  - gpt-4o-mini, claude, etc.
└─────────────────┘
```

---

## Useful Commands

```bash
# API
cd api
alembic upgrade head      # Apply migrations
alembic revision -m "..."  # Create migration
pytest                     # Run tests
uvicorn app.main:app --reload --port 8001  # Start API

# Console
cd console
npm run dev               # Start dev server
npm run build             # Production build
npm run lint              # Lint code

# Database
docker compose up -d db   # Start PostgreSQL
docker compose down       # Stop all services
psql postgresql://kyros:kyros@localhost:5432/kyros  # Connect to DB
```

---

## Configuration Files

- `api/.env` - API configuration (JWT, database, OpenRouter)
- `console/.env.local` - Console configuration (API URL)
- `api/alembic.ini` - Database migration settings
- `api/docker-compose.yml` - PostgreSQL service

---

## Default Ports

- **Console**: 3000
- **API**: 8001
- **PostgreSQL**: 5432

---

## Getting Help

1. Check the docs:
   - [README.md](README.md) - Main readme
   - [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture overview
   - [api/README.md](api/README.md) - API details
   - [api/AUTH_API.md](api/AUTH_API.md) - Authentication guide

2. View API docs: http://localhost:8001/docs (Swagger UI)

3. Check logs:
   ```bash
   # API logs (stdout)
   cd api && uvicorn app.main:app --reload

   # Database logs
   docker compose logs -f db
   ```

---

Happy building! 🚀
