# Kyros Praxis User Guide

This comprehensive user guide provides step-by-step instructions for getting started with Kyros Praxis, from initial setup to advanced usage scenarios.

## 📚 Table of Contents

- [Getting Started](#getting-started)
- [Service Overview](#service-overview)
- [Development Workflow](#development-workflow)
- [API Usage](#api-usage)
- [Terminal Operations](#terminal-operations)
- [Security Features](#security-features)
- [Advanced Configuration](#advanced-configuration)
- [Common Use Cases](#common-use-cases)

## 🚀 Getting Started

### System Requirements

**Minimum Requirements:**
- 8GB RAM
- 4 CPU cores
- 20GB available disk space
- Docker Engine 20.10+
- Docker Compose v2.0+

**Recommended:**
- 16GB RAM
- 8 CPU cores
- 50GB available disk space
- SSD storage for better performance

### Initial Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/tdawe1/kyros-praxis.git
   cd kyros-praxis
   ```

2. **Environment Configuration**
   ```bash
   # Copy example environment files
   cp services/orchestrator/.env.example services/orchestrator/.env
   cp services/console/.env.example services/console/.env
   cp services/terminal-daemon/.env.example services/terminal-daemon/.env
   ```

3. **Configure Essential Settings**
   
   **Orchestrator Service (`services/orchestrator/.env`):**
   ```env
   # Database
   DATABASE_URL=postgresql://kyros:kyros_pass@localhost:5432/kyros_db
   
   # Security
   SECRET_KEY=your_very_secure_secret_minimum_32_chars
   JWT_SECRET=your_jwt_secret_minimum_32_chars
   
   # CORS
   BACKEND_CORS_ORIGINS=["http://localhost:3001"]
   ```
   
   **Console Service (`services/console/.env`):**
   ```env
   NEXTAUTH_URL=http://localhost:3001
   NEXTAUTH_SECRET=your_nextauth_secret
   ORCHESTRATOR_URL=http://localhost:8000
   ```
   
   **Terminal Daemon (`services/terminal-daemon/.env`):**
   ```env
   PORT=8787
   JWT_SECRET=your_jwt_secret_minimum_32_chars
   ALLOWED_ORIGINS=http://localhost:3001
   ORCHESTRATOR_URL=http://localhost:8000
   ```

4. **Start Services**
   ```bash
   # Start all services with Docker Compose
   docker compose up -d
   
   # Or start services individually for development
   # Start infrastructure first
   docker compose up -d postgres redis
   
   # Then start each service in separate terminals
   cd services/orchestrator && python -m uvicorn main:app --reload
   cd services/console && npm run dev
   cd services/terminal-daemon && npm start
   ```

5. **Verify Installation**
   ```bash
   # Check service health
   curl http://localhost:8000/health      # Orchestrator
   curl http://localhost:3001             # Console
   curl http://localhost:8787/health      # Terminal Daemon
   ```

## 🏗️ Service Overview

### Console (Frontend)
**Purpose:** User interface for managing AI orchestration tasks, viewing system status, and interacting with terminal sessions.

**Key Features:**
- Dashboard with system overview
- Job management and monitoring
- Real-time terminal access
- User authentication and profile management
- System configuration interface

**Access:** http://localhost:3001

### Orchestrator (Backend API)
**Purpose:** Core business logic, job scheduling, and coordination between services.

**Key Features:**
- RESTful API for all platform operations
- Job scheduling and workflow management
- User authentication and authorization
- Event handling and notifications
- Database management and migrations

**Access:** 
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- OpenAPI spec: http://localhost:8000/api/v1/openapi.json

### Terminal Daemon
**Purpose:** WebSocket-based terminal service for remote command execution.

**Key Features:**
- Real-time terminal sessions via WebSocket
- Secure command execution with JWT authentication
- Session management and persistence
- Resource monitoring and limits

**Access:** ws://localhost:8787

## 🔄 Development Workflow

### 1. Feature Development
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Start development environment
docker compose up -d postgres redis

# Start services in development mode
cd services/orchestrator && python -m uvicorn main:app --reload &
cd services/console && npm run dev &
cd services/terminal-daemon && npm run dev &
```

### 2. Testing
```bash
# Run all tests
python3 scripts/pr_gate.py --run-tests

# Run specific service tests
cd services/orchestrator && python -m pytest
cd services/console && npm test
cd services/terminal-daemon && npm test
```

### 3. Code Quality
```bash
# Lint Python code
ruff check services/orchestrator

# Lint frontend code
cd services/console && npm run lint

# Fix linting issues automatically
ruff check --fix services/orchestrator
cd services/console && npm run lint:fix
```

## 🔗 API Usage

### Authentication Flow
1. **Login to get access token:**
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin"}'
   ```

2. **Use token for authenticated requests:**
   ```bash
   export TOKEN="your_access_token"
   curl -X GET http://localhost:8000/api/v1/jobs \
     -H "Authorization: Bearer $TOKEN"
   ```

### Common API Operations

#### Job Management
```bash
# List all jobs
curl -X GET http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer $TOKEN"

# Create a new job
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Example Job",
    "description": "Job description",
    "status": "pending"
  }'

# Get job details
curl -X GET http://localhost:8000/api/v1/jobs/{job_id} \
  -H "Authorization: Bearer $TOKEN"
```

#### System Monitoring
```bash
# Get system metrics
curl -X GET http://localhost:8000/api/v1/monitoring/metrics \
  -H "Authorization: Bearer $TOKEN"

# Check security configuration
curl -X GET http://localhost:8000/api/v1/security/config \
  -H "Authorization: Bearer $TOKEN"
```

## 💻 Terminal Operations

### WebSocket Connection
```javascript
// Connect to terminal daemon
const ws = new WebSocket('ws://localhost:8787', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

// Send commands
ws.send(JSON.stringify({
  type: 'command',
  data: 'ls -la'
}));

// Receive output
ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  console.log(response.data);
};
```

### Terminal Features
- **Session Management:** Multiple concurrent terminal sessions
- **Command History:** Persistent command history per session
- **Resource Limits:** Configurable memory and CPU limits
- **Security:** JWT-based authentication for all terminal access

## 🛡️ Security Features

### Authentication & Authorization
- **JWT Tokens:** Secure, stateless authentication
- **Role-Based Access:** Configurable user roles and permissions
- **Token Expiration:** Configurable token lifetime (default: 30 minutes)
- **Secure Storage:** Environment-based secret management

### Network Security
- **CORS Protection:** Configurable cross-origin request policies
- **CSRF Protection:** Token-based CSRF prevention
- **Rate Limiting:** Configurable request throttling
- **HTTPS Enforcement:** Automatic HTTPS redirect in production

### Data Security
- **Parameterized Queries:** SQL injection prevention
- **Input Validation:** Comprehensive request validation
- **Error Handling:** Structured error responses without information leakage
- **Audit Logging:** Comprehensive activity logging

## ⚙️ Advanced Configuration

### Environment Variables
Each service supports extensive configuration through environment variables:

#### Orchestrator Configuration
```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://user:pass@host:port/db
DATABASE_POOL_SIZE=20

# Security
SECRET_KEY=your_secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3001"]

# Logging
LOG_LEVEL=INFO
LOG_FILE=orchestrator.log
```

#### Console Configuration
```env
# NextAuth
NEXTAUTH_URL=http://localhost:3001
NEXTAUTH_SECRET=your_secret

# API Configuration
ORCHESTRATOR_URL=http://localhost:8000
TERMINAL_DAEMON_URL=ws://localhost:8787

# Features
ENABLE_ANALYTICS=false
ENABLE_DEBUG_MODE=true
```

#### Terminal Daemon Configuration
```env
# Server
PORT=8787
NODE_ENV=development

# Security
JWT_SECRET=your_secret
ALLOWED_ORIGINS=http://localhost:3001

# Resource Limits
MAX_SESSIONS=100
SESSION_TIMEOUT=3600
MAX_COMMAND_LENGTH=10000

# Logging
LOG_LEVEL=info
```

### Database Configuration
```bash
# Run migrations
cd services/orchestrator
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Rollback migration
alembic downgrade -1
```

## 🎯 Common Use Cases

### 1. Job Orchestration
**Scenario:** Schedule and monitor background tasks

```bash
# Create a job
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Data Processing Job",
    "description": "Process daily analytics data",
    "schedule": "0 2 * * *",
    "command": "python process_data.py"
  }'

# Monitor job status
curl -X GET http://localhost:8000/api/v1/jobs/{job_id}/status \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Remote Terminal Access
**Scenario:** Execute commands remotely through the web interface

1. Open the Console at http://localhost:3001
2. Navigate to Terminal section
3. Click "New Terminal Session"
4. Execute commands in the interactive terminal

### 3. System Monitoring
**Scenario:** Monitor system health and performance

```bash
# Get system metrics
curl -X GET http://localhost:8000/api/v1/monitoring/metrics \
  -H "Authorization: Bearer $TOKEN"

# Get service health
curl -X GET http://localhost:8000/api/v1/monitoring/health \
  -H "Authorization: Bearer $TOKEN"
```

### 4. User Management
**Scenario:** Add new users and manage permissions

```bash
# Create new user (admin required)
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "username": "newuser",
    "email": "user@example.com",
    "password": "secure_password",
    "role": "user"
  }'

# Update user permissions
curl -X PUT http://localhost:8000/api/v1/users/{user_id}/role \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"role": "admin"}'
```

## 🔗 Next Steps

- [API Documentation](../api/README.md) - Detailed API reference
- [Architecture Overview](../architecture/overview.md) - System design details
- [Security Guidelines](../security/README.md) - Security best practices
- [Operations Manual](../ops/runbooks/README.md) - Deployment and operations
- [Troubleshooting Guide](../troubleshooting/) - Common issues and solutions
- [FAQ](../faq/) - Frequently asked questions