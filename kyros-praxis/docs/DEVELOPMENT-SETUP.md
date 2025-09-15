# Development Environment Setup Guide

This guide provides comprehensive instructions for setting up the Kyros Praxis development environment.

## Quick Start

For automated setup, run:

```bash
# Clone the repository
git clone https://github.com/tdawe1/kyros-praxis.git
cd kyros-praxis

# Run the automated setup script
./scripts/setup-dev-env.sh
```

The automated script will:
- Install system dependencies (Docker, Python, Node.js)
- Configure environment files with secure secrets
- Install Python and Node.js dependencies
- Set up initial collaboration state
- Start infrastructure services (PostgreSQL, Redis)
- Run verification checks

## Manual Setup

### 1. Prerequisites

#### System Requirements
- **Operating System**: Linux (Ubuntu/Debian recommended), macOS, or Windows (WSL2)
- **RAM**: Minimum 8GB, recommended 16GB
- **Storage**: Minimum 10GB free space
- **CPU**: Modern multi-core processor

#### Install Docker and Docker Compose

**Ubuntu/Debian:**
```bash
# Update package index
sudo apt update

# Install Docker
sudo apt install docker.io docker-compose

# Add user to docker group (log out and back in after this)
sudo usermod -aG docker $USER

# Verify installation
docker --version
docker-compose --version
```

**macOS:**
- Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)

**Windows:**
- Install WSL2 first, then Docker Desktop for Windows

#### Install Python 3.11+

**Ubuntu/Debian:**
```bash
sudo apt install python3.11 python3.11-venv python3-pip
python3 --version
```

**macOS (using Homebrew):**
```bash
brew install python@3.11
```

#### Install Node.js 18+

**Ubuntu/Debian (using NodeSource):**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs
node --version
npm --version
```

**macOS (using Homebrew):**
```bash
brew install node@18
```

#### Install Additional Tools

```bash
# Git (usually pre-installed)
sudo apt install git

# UV (Python package manager)
pip install uv

# NPX (Node package runner)
npm install -g npx
```

### 2. Repository Setup

```bash
# Clone the repository
git clone https://github.com/tdawe1/kyros-praxis.git
cd kyros-praxis

# Copy environment configuration files
cp services/orchestrator/.env.example services/orchestrator/.env
cp services/console/.env.example services/console/.env
cp services/terminal-daemon/.env.example services/terminal-daemon/.env

# Generate secure secrets (minimum 32 characters)
openssl rand -hex 32
```

### 3. Environment Configuration

#### Orchestrator Service (`services/orchestrator/.env`)

```env
# Security (generate with: openssl rand -hex 32)
SECRET_KEY=your_generated_secret_key_here
JWT_SECRET=your_generated_jwt_secret_here
JWT_ALGORITHM=HS512
JWT_ISSUER=kyros-praxis
JWT_AUDIENCE=kyros-app

# Database
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_db_password
POSTGRES_DB=kyros

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_secure_redis_password

# AI Service Keys (obtain from respective providers)
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

#### Console Service (`services/console/.env`)

```env
# Authentication
NEXTAUTH_SECRET=your_generated_nextauth_secret_here
NEXTAUTH_URL=http://localhost:3000

# API Configuration
NEXT_PUBLIC_ADK_URL=http://localhost:8000
KYROS_DAEMON_PORT=8787

# AI Model Configuration
MODEL_PLANNER=gpt-5-high
MODEL_IMPL=gemini-2.5-pro
MODEL_DEEP=claude-4-sonnet
MODEL_ARCH=claude-4.1-opus
```

### 4. MCP Server Configuration

#### Basic MCP Setup

```bash
# Copy MCP configuration template
cp mcp.example.json mcp.json

# Edit mcp.json to enable required servers
# Comment out servers you don't need
```

#### Configure Essential MCP Servers

1. **Filesystem MCP**:
   ```json
   "filesystem": {
     "command": "npx",
     "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
   }
   ```

2. **Git MCP**:
   ```json
   "git": {
     "command": "uvx",
     "args": ["mcp-server-git", "--repository", "."]
   }
   ```

3. **Time MCP**:
   ```json
   "time": {
     "command": "uvx",
     "args": ["mcp-server-time"]
   }
   ```

#### Test MCP Servers

```bash
# Test filesystem MCP
npx -y @modelcontextprotocol/server-filesystem . --help

# Test time MCP
uvx mcp-server-time --help

# Test git MCP (if in a git repository)
uvx mcp-server-git --repository . --help
```

### 5. Start Infrastructure Services

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Verify services are running
docker-compose ps

# Check logs if needed
docker-compose logs postgres
docker-compose logs redis
```

### 6. Install Dependencies

#### Python Dependencies

```bash
cd services/orchestrator
pip install -r requirements.txt
cd ../..
```

#### Node.js Dependencies

```bash
# Console service
cd services/console
npm install
cd ../..

# Terminal daemon
cd services/terminal-daemon
npm install
cd ../..
```

### 7. Initialize Collaboration State

```bash
# Create collaboration directories
mkdir -p collaboration/state
mkdir -p collaboration/events

# Initialize tasks.json
cat > collaboration/state/tasks.json << 'EOF'
{
  "tasks": [
    {
      "id": "TDS-1",
      "title": "Implement collab API steel thread",
      "status": "todo",
      "priority": "P0",
      "created_at": "2025-09-14T10:00:00Z"
    },
    {
      "id": "TDS-3",
      "title": "Implement Jobs vertical slice",
      "status": "todo",
      "priority": "P0",
      "created_at": "2025-09-14T10:00:00Z"
    }
  ]
}
EOF

# Initialize events file
touch collaboration/events/events.jsonl
```

### 8. Start Development Services

#### Orchestrator (Backend API)

```bash
cd services/orchestrator
PYTHONPATH=. uvicorn main:app --reload --port 8000
```

In a new terminal, verify it's running:
```bash
curl http://localhost:8000/healthz
```

#### Console (Frontend)

```bash
cd services/console
npm run dev
```

Access at http://localhost:3001

#### Terminal Daemon

```bash
cd services/terminal-daemon
npm start
```

Runs on ws://localhost:8787

### 9. Verification

Run the verification script to check your setup:

```bash
python scripts/verify-setup.py
```

This will check:
- System dependencies
- Docker services
- Environment configuration
- Installed dependencies
- Port availability
- API health

## Development Workflow

### Daily Development

1. **Start services**:
   ```bash
   # Start infrastructure
   docker-compose up -d

   # Start backend
   cd services/orchestrator && uvicorn main:app --reload

   # Start frontend (in another terminal)
   cd services/console && npm run dev
   ```

2. **Run tests**:
   ```bash
   # Backend tests
   cd services/orchestrator && python -m pytest

   # Frontend tests
   cd services/console && npm test

   # E2E tests
   cd services/console && npm run test:e2e
   ```

3. **Code quality checks**:
   ```bash
   # Run PR gate checks
   python scripts/pr_gate_minimal.py
   ```

### Collaboration Workflow

1. **Update task status**:
   ```bash
   # Get current ETag
   python scripts/state_update.py --show-etag

   # Update task status
   python scripts/state_update.py TDS-1 in_progress --if-match "$ETAG" --user "developer"
   ```

2. **View task list**:
   ```bash
   python scripts/state_update.py --list
   ```

3. **Check events**:
   ```bash
   cat collaboration/events/events.jsonl
   ```

### MCP Server Usage

#### Using MCP with Claude Code

1. **Configure MCP servers** in your Claude Code settings:
   ```json
   {
     "mcpServers": {
       "filesystem": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
       },
       "git": {
         "command": "uvx",
         "args": ["mcp-server-git", "--repository", "."]
       }
     }
   }
   ```

2. **Available MCP tools**:
   - Filesystem operations: read, write, list files
   - Git operations: commit, diff, log
   - Time operations: get current time, format dates
   - Database operations (if configured)
   - Web scraping (if configured)

## Troubleshooting

### Common Issues

#### Port Conflicts

If ports are already in use:
```bash
# Check what's using a port
lsof -i :8000
ss -tlnp | grep :8000

# Kill the process using the port
kill -9 <PID>
```

#### Docker Issues

```bash
# Reset Docker environment
docker-compose down
docker system prune -a
docker-compose up -d

# Check Docker logs
docker-compose logs <service>
```

#### Python Environment Issues

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# If packages conflict:
pip install --force-reinstall -r requirements.txt
```

#### Node.js Issues

```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### Database Connection Issues

```bash
# Check PostgreSQL status
docker-compose ps postgres

# Reset database
docker-compose down postgres
docker volume rm kyros-praxis_postgres_data
docker-compose up -d postgres
```

### Getting Help

1. **Check logs**:
   - Orchestrator: `services/orchestrator/orchestrator.log`
   - Console: Check browser console
   - Docker: `docker-compose logs`

2. **Run diagnostics**:
   ```bash
   python scripts/verify-setup.py
   ```

3. **Community support**:
   - GitHub Issues: [Create an issue](https://github.com/tdawe1/kyros-praxis/issues)
   - Documentation: Check the `docs/` directory for specific guides

## Production Deployment

For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md) (not yet created).

Key differences for production:
- Use environment-specific .env files
- Generate new secure secrets
- Configure proper CORS origins
- Set up reverse proxy (nginx)
- Configure SSL/TLS certificates
- Set up monitoring and logging
- Use container orchestration (Kubernetes)

## Contributing

Before contributing:
1. Run all tests: `make test`
2. Run linting: `make lint`
3. Run PR gate: `python scripts/pr_gate_minimal.py`
4. Update documentation as needed

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

*Last updated: September 14, 2025*