# Kyros Orchestrator Service

The Kyros Orchestrator is the core backend service of the Kyros Praxis platform, providing business logic orchestration, job management, and API coordination between all system components.

## 🏗️ Architecture

### Technology Stack
- **FastAPI** with Python 3.11+
- **SQLAlchemy** with async PostgreSQL
- **Alembic** for database migrations
- **JWT** authentication
- **Redis** for caching and session management
- **Pydantic** for data validation
- **WebSockets** for real-time communication

### Core Responsibilities
- **Job Orchestration**: Manage AI agent job lifecycle
- **API Gateway**: Central entry point for all operations
- **Authentication**: User authentication and authorization
- **Real-time Updates**: WebSocket support for live updates
- **Business Logic**: Core platform workflow execution
- **Service Coordination**: Integration with other services

## 🚀 Development Setup

### Prerequisites
- Python 3.11 or higher
- PostgreSQL database (development can use SQLite)
- Redis server (optional, for caching)
- pip package manager

### Installation

1. **Navigate to service directory**:
   ```bash
   cd services/orchestrator
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**:
   ```bash
   cp .env.example .env
   ```

4. **Configure environment variables**:
   ```bash
   # Required
   SECRET_KEY=your_very_secure_secret_minimum_32_chars
   DATABASE_URL=postgresql://user:password@localhost:5432/kyros
   REDIS_URL=redis://localhost:6379
   ALLOWED_ORIGINS=http://localhost:3001
   
   # Optional
   DEBUG=True
   LOG_LEVEL=INFO
   ```

5. **Generate secure secret key**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

6. **Run database migrations** (if using PostgreSQL):
   ```bash
   alembic upgrade head
   ```

### Running the Service

**Development Mode**:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Production Mode**:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Testing API Connectivity

1. **Health Check**:
   ```bash
   curl http://localhost:8000/healthz
   ```

2. **Authentication Test**:
   ```bash
   # Get JWT token
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=test@example.com&password=password"
   ```

3. **Create Job Test**:
   ```bash
   # Replace JWT_TOKEN with actual token
   curl -X POST http://localhost:8000/api/v1/jobs \
     -H "Authorization: Bearer JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"title":"Test Job"}'
   ```

## 📁 Project Structure

```
services/orchestrator/
├── main.py              # FastAPI application entry point
├── app/
│   ├── core/
│   │   └── config.py    # Application configuration
│   └── routers/         # API route modules
├── routers/             # API route definitions
│   ├── jobs.py         # Job management endpoints
│   ├── tasks.py        # Task management endpoints
│   ├── utils.py        # Utility endpoints
│   └── events.py       # Event handling endpoints
├── models.py           # SQLAlchemy database models
├── database.py         # Database connection and session management
├── auth.py            # Authentication and authorization logic
├── security_middleware.py # Security middleware implementation
├── utils/
│   └── validation.py   # Input validation utilities
├── repositories/       # Data access layer
└── tests/             # Test suite
```

## 🔧 API Endpoints

### Health Check
- `GET /health` - Basic health check
- `GET /healthz` - Health check with database connectivity

### Authentication
- `POST /auth/login` - User authentication, returns JWT token

### Jobs API (`/api/v1/jobs`)
- `POST /api/v1/jobs` - Create new job
- `GET /api/v1/jobs` - List all jobs
- `GET /api/v1/jobs/{job_id}` - Get specific job
- `DELETE /api/v1/jobs/{job_id}` - Delete job (not implemented)

### Tasks API (`/api/v1/collab`)
- `POST /api/v1/collab/tasks` - Create new task
- `GET /api/v1/collab/state/tasks` - List all tasks

### Utilities API (`/api/v1/utils`)
- Various utility endpoints for internal operations

### WebSocket
- `WS /ws` - Real-time communication endpoint

## 🔐 Authentication

### JWT Implementation
- Algorithm: HS256
- Token expiration: 30 minutes (configurable)
- Secret key from environment variable
- User authentication via email/password

### Security Features
- Password hashing with bcrypt
- CORS configuration
- Request rate limiting
- SQL injection prevention
- Input validation with Pydantic

## 🗄️ Database Schema

### Core Models
```python
class User(Base):
    id: UUID
    email: str (unique)
    password_hash: str

class Job(Base):
    id: UUID
    name: str
    status: str
    created_at: datetime

class Task(Base):
    id: UUID
    title: str
    description: str
    version: int
    created_at: datetime

class Event(Base):
    id: UUID
    type: str
    payload: JSON
    created_at: datetime
```

### Database Configuration
- **Development**: SQLite in-memory for quick iteration
- **Production**: PostgreSQL with connection pooling
- **Migrations**: Alembic for schema versioning
- **Backups**: Automated backups in production

## 🔧 Development Commands

```bash
# Development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Database operations
alembic upgrade head        # Apply migrations
alembic revision --autogenerate -m "description"  # Create migration
alembic downgrade -1       # Rollback last migration

# Testing
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest --cov=app          # With coverage report

# Type checking
mypy .                    # Static type checking

# Linting
flake8 .                  # Code style checking
black .                   # Code formatting
```

## 🧪 Testing

### Test Structure
```
tests/
├── unit/                 # Unit tests
├── integration/          # Integration tests
├── e2e/                  # End-to-end tests
└── conftest.py          # Test configuration
```

### Running Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/test_jobs.py

# With coverage
pytest --cov=app --cov-report=html

# Run specific test category
pytest -m unit
pytest -m integration
```

## 🚀 Deployment

### Environment Variables
Required for production deployment:

```bash
# Security
SECRET_KEY=your_production_secret
DEBUG=False

# Database
DATABASE_URL=postgresql://user:password@prod-db:5432/kyros

# Redis
REDIS_URL=redis://prod-redis:6379

# CORS
ALLOWED_ORIGINS=https://your-domain.com

# Logging
LOG_LEVEL=INFO
```

### Docker Deployment
```dockerfile
# Build image
docker build -t kyros-orchestrator .

# Run container
docker run -p 8000:8000 \
  -e SECRET_KEY=your_secret \
  -e DATABASE_URL=your_db_url \
  kyros-orchestrator
```

### Docker Compose
```yaml
services:
  orchestrator:
    build: ./services/orchestrator
    ports:
      - "8000:8000"
    environment:
      - SECRET_KEY=your_secret
      - DATABASE_URL=postgresql://postgres:password@db:5432/kyros
    depends_on:
      - db
      - redis
```

## 🔧 Troubleshooting

### Common Issues

**Database Connection Issues**
```bash
# Check database connectivity
pg_isready -d your_database -h your_host -p your_port

# Test SQLAlchemy connection
python -c "from database import engine; print(engine.connect())"
```

**Migration Issues**
```bash
# Check migration status
alembic current
alembic history

# Reset database (development only)
alembic downgrade base
alembic upgrade head
```

**JWT Authentication Issues**
1. Verify `SECRET_KEY` matches between services
2. Check token expiration time
3. Verify user exists in database
4. Check CORS settings

**Performance Issues**
```bash
# Check database queries
export DEBUG_SQL=1
uvicorn main:app --reload

# Monitor memory usage
python -m memory_profiler main.py
```

### Debug Mode
Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
uvicorn main:app --reload
```

## 📊 Monitoring & Observability

### Health Checks
- `/health` - Basic health
- `/healthz` - Health with database connectivity
- `/metrics` - Application metrics (if configured)

### Logging
- Structured JSON logging in production
- Request/response logging
- Error tracking with stack traces
- Security event logging

### Metrics (Optional)
- Request latency and throughput
- Database query performance
- Error rates by endpoint
- System resource usage

## 🛡️ Security Considerations

### Current Security Features
- JWT authentication with secure secrets
- Input validation and sanitization
- SQL injection prevention
- CORS protection
- Rate limiting (configurable)

### Security Best Practices
1. Always use strong, randomly generated secrets
2. Implement proper CORS policies for production
3. Use HTTPS in production environments
4. Regular security audits and dependency updates
5. Implement proper error handling without information leakage

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://www.sqlalchemy.org/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Project API Documentation](../../docs/api/README.md)
- [Overall Architecture](../../docs/architecture/overview.md)