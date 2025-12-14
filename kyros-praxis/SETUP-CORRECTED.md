# Kyros Praxis Development Environment Setup

This document provides the corrected development environment setup instructions based on the actual repository structure.

## Repository Structure

The repository uses the following structure:
- `services/orchestrator/` - FastAPI backend service
- `services/console/` - Next.js frontend service
- `services/terminal-daemon/` - WebSocket terminal service
- Root directory - Express server and client

## Prerequisites

### System Requirements

- **Node.js 20+**
  ```bash
  node -v && npm -v
  # Install (Ubuntu):
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs
  ```

- **Python 3.11+**
  ```bash
  python3 --version
  sudo apt install -y python3.11 python3.11-venv python3-pip
  ```

- **Git**
  ```bash
  git --version
  ```

- **Optional**: Docker if you plan to run extra services (not required for core dev)

## Clone & Install

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url> && cd kyros-praxis
   ```

2. **Install Node dependencies**:
   ```bash
   npm ci --legacy-peer-deps
   ```

3. **Install Orchestrator dependencies**:
   ```bash
   pip install -r services/orchestrator/requirements.txt
   ```

4. **Install Terminal daemon dependencies**:
   ```bash
   cd services/terminal-daemon && npm install && cd -
   ```

## Environment Configuration

### 1. Orchestrator (FastAPI)

Create `services/orchestrator/.env`:

```env
# JWT Configuration
JWT_SECRET=<strong-secret>  # Generate with: openssl rand -hex 32
JWT_ISSUER=kyros-praxis     # Optional
JWT_AUDIENCE=kyros-app      # Optional

# Optional Basic Auth
ORCH_AUTH_USER=admin        # Optional
ORCH_AUTH_PASS=password    # Optional

# CORS Configuration
CORS_ALLOW_ORIGINS=http://localhost:3001,http://localhost:5000

# Database (SQLite by default)
DATABASE_URL=sqlite:///./orchestrator.db
```

### 2. Terminal Daemon (WebSocket)

Create `services/terminal-daemon/.env`:

```env
# JWT Secret (use same as orchestrator)
TERMINAL_JWT_SECRET=<same-strong-secret>

# Port Configuration
KYROS_DAEMON_PORT=8787
```

### 3. Root Server (Express)

Set environment variables when running:

```bash
# Required
ALLOWED_ORIGINS=http://localhost:3001,http://localhost:5000
COOKIE_SECRET=change-me-secure-secret

# Optional
PORT=5000
```

### 4. Generate Dev JWT Token (Optional, for WS Auth)

```bash
# Set the JWT secret
export JWT_SECRET=<same-strong-secret>

# Generate token
npm run gen:jwt > dev.jwt

# Set in browser (for WebSocket authentication)
# In browser console:
document.cookie = "auth_token=$(cat dev.jwt); path=/";
```

## Run Services

### Option 1: Individual Services

1. **Start Orchestrator**:
   ```bash
   cd services/orchestrator
   PYTHONPATH=. uvicorn main:app --reload --port 8000
   # Health check: http://localhost:8000/healthz
   ```

2. **Start Terminal daemon**:
   ```bash
   cd services/terminal-daemon
   npm run dev
   # Runs on ws://localhost:8787
   ```

3. **Start Root Server**:
   ```bash
   npm run dev
   # Runs on http://localhost:5000
   ```

### Option 2: Using Provided Scripts

```bash
# Start orchestrator
./start-orchestrator.sh

# Start console (from another terminal)
./start-console.sh

# Start terminal daemon (from another terminal)
./start-daemon.sh
```

### Option 3: Using the Workflow Script

```bash
# Start all services
./dev-workflow.sh start

# Check status
./dev-workflow.sh status

# View logs
./dev-workflow.sh logs
```

## Terminal Connection

1. Open the application in your browser: http://localhost:5000
2. Navigate to the "Terminal" page
3. Click "Connect"
   - Uses wss:// on HTTPS
   - Appends ?token= if JWT token is present in cookies

## Testing & QA

### Type Checks
```bash
npm run check
```

### Python Tests
```bash
npm run test:python
# Or directly:
cd services/orchestrator && python -m pytest
```

### E2E Tests
```bash
# Build the application
npm run build

# Install Playwright browsers
npm run e2e:install

# Start server (in another terminal)
npm run start

# Run E2E tests
npm run e2e
```

### API Spec Validation
```bash
npm run validate:api
```

## CI/CD

The GitHub Actions workflow (`.github/workflows/ci.yml`) includes:
- Installs dependencies
- Builds the application
- Runs Python tests
- Starts server and runs Playwright E2E tests
- Runs API spec validation
- Security checks:
  - Semgrep (best effort)
  - pip-audit

**Note**: No Docker Compose is needed for the core stack. The project defaults to SQLite.

## Security Notes

- **Secrets**: Never commit secrets to the repository. Use `.env` files or export environment variables in your shell.
- **Orchestrator**: Enforces security headers and optional Basic/JWT authentication
- **Express Server**: Enforces Helmet (in production), CORS, CSRF, and rate limiting
- **Terminal Daemon**: Can require HS512 JWT via `TERMINAL_JWT_SECRET` (reuse from orchestrator for convenience)

## Common Issues

### Port Conflicts
If ports are already in use:
```bash
# Check what's using a port
lsof -i :8000
# Kill the process
kill -9 <PID>
```

### Python Virtual Environment
```bash
# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r services/orchestrator/requirements.txt
```

### Dependency Issues
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm ci --legacy-peer-deps
```

## Architecture Overview

1. **Orchestrator** (Port 8000): FastAPI backend with job management, authentication, and API endpoints
2. **Terminal Daemon** (Port 8787): WebSocket service for terminal sessions
3. **Root Server** (Port 5000): Express server serving the web UI and proxying to services

## Need Help?

- Check logs in each service directory
- Run verification: `python scripts/verify-setup.py`
- See documentation in the `docs/` directory

---

*Last updated: September 15, 2025*