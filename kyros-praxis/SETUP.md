# Quick Development Setup

This document provides quick setup instructions for the Kyros Praxis development environment.

## Repository Structure

This repository uses:
- `services/orchestrator/` - FastAPI backend service
- `services/console/` - Next.js frontend service
- `services/terminal-daemon/` - WebSocket terminal service
- Root directory - Express server and client

## Setup Options

### Option 1: Automated Setup (Recommended)

For new developers, run the corrected setup script:

```bash
# Clone the repository
git clone <your-repo-url> && cd kyros-praxis

# Run corrected setup
./scripts/setup-corrected.sh
```

### Option 2: Manual Setup

Already have the dependencies? Follow these steps:

1. Install dependencies:
   ```bash
   npm ci --legacy-peer-deps
   pip install -r services/orchestrator/requirements.txt
   cd services/terminal-daemon && npm install && cd -
   ```

2. Create environment files (see SETUP-CORRECTED.md for details)

## Development Workflow

### Starting Services

```bash
# Option 1: Use the workflow script
./dev-workflow.sh start

# Option 2: Use Make
make start

# Option 3: Start individually
./start-orchestrator.sh &
./start-console.sh &
./start-daemon.sh &
```

### Daily Development

```bash
# Check service status
./dev-workflow.sh status

# View logs
./dev-workflow.sh logs orchestrator

# Run tests
make test

# Update task status
./dev-workflow.sh update-task TDS-1 in_progress

# List tasks
./dev-workflow.sh list-tasks
```

### Stopping Services

```bash
# Stop all services
./dev-workflow.sh stop

# Or using Make
make stop
```

## Verification

Verify your setup is working:

```bash
# Comprehensive verification
python scripts/verify-setup.py

# Quick health check
curl http://localhost:8000/healthz
```

## Manual Commands

### Without Scripts

```bash
# Start infrastructure
docker-compose up -d postgres redis

# Start backend
cd services/orchestrator
PYTHONPATH=. uvicorn main:app --reload --port 8000

# Start frontend (new terminal)
cd services/console
npm run dev

# Start terminal daemon (new terminal)
cd services/terminal-daemon
npm start
```

### Common Issues

**Port conflicts:**
```bash
# Check what's using port 8000
lsof -i :8000
# Kill the process
kill -9 <PID>
```

**Permission issues:**
```bash
# Add user to docker group (logout/in after)
sudo usermod -aG docker $USER
```

**Missing dependencies:**
```bash
# Python
pip install -r services/orchestrator/requirements.txt

# Node.js
cd services/console && npm install
cd services/terminal-daemon && npm install
```

## Service URLs

- **Orchestrator API**: http://localhost:8000
  - API docs: http://localhost:8000/docs
  - Health check: http://localhost:8000/healthz

- **Console Frontend**: http://localhost:3001

- **Terminal Daemon**: ws://localhost:8787

## Next Steps

1. Read the full setup guide: `docs/DEVELOPMENT-SETUP.md`
2. Configure your MCP servers in `mcp.json`
3. Check out the architecture documentation in `docs/`
4. Run the verification: `python scripts/verify-setup.py`

## Need Help?

- Check logs: `./dev-workflow.sh logs`
- Run diagnostics: `make verify`
- See full docs: `docs/DEVELOPMENT-SETUP.md`

---

*Happy coding! 🚀*