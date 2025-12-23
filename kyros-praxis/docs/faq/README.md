# Frequently Asked Questions (FAQ)

This FAQ addresses common questions about Kyros Praxis setup, configuration, usage, and troubleshooting.

## 📚 Table of Contents

- [Getting Started](#getting-started)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Development](#development)
- [API Usage](#api-usage)
- [Security](#security)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)

## 🚀 Getting Started

### Q: What is Kyros Praxis?
**A:** Kyros Praxis is a sophisticated multi-service AI orchestration platform that provides intelligent agent management, real-time terminal operations, and collaborative development workflows with enterprise-grade security and observability.

### Q: What are the main components?
**A:** The platform consists of:
- **Console** - Next.js frontend with Carbon Design System
- **Orchestrator** - FastAPI backend with SQLAlchemy & PostgreSQL
- **Terminal Daemon** - WebSocket terminal service (Node.js + node-pty)
- **Service Registry** - Service discovery and health monitoring
- **Zen MCP Server** - AI model coordination and workflow execution

### Q: What are the system requirements?
**A:** 
**Minimum:**
- 8GB RAM, 4 CPU cores, 20GB disk space
- Docker Engine 20.10+, Docker Compose v2.0+

**Recommended:**
- 16GB RAM, 8 CPU cores, 50GB disk space
- SSD storage for better performance

## 🛠️ Installation & Setup

### Q: How do I get started quickly?
**A:** 
```bash
# Clone and start with Docker Compose
git clone https://github.com/tdawe1/kyros-praxis.git
cd kyros-praxis
docker compose up -d

# Services will be available at:
# Console: http://localhost:3001
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Q: How do I set up for development?
**A:**
```bash
# Start infrastructure services
docker compose up -d postgres redis

# Start services individually for development
cd services/orchestrator && python -m uvicorn main:app --reload
cd services/console && npm run dev
cd services/terminal-daemon && npm start
```

### Q: What environment variables do I need to configure?
**A:** Essential environment variables:

**Orchestrator (.env):**
```env
DATABASE_URL=postgresql://kyros:kyros_pass@localhost:5432/kyros_db
SECRET_KEY=your_very_secure_secret_minimum_32_chars
JWT_SECRET=your_jwt_secret_minimum_32_chars
BACKEND_CORS_ORIGINS=["http://localhost:3001"]
```

**Console (.env):**
```env
NEXTAUTH_URL=http://localhost:3001
NEXTAUTH_SECRET=your_nextauth_secret
ORCHESTRATOR_URL=http://localhost:8000
```

**Terminal Daemon (.env):**
```env
PORT=8787
JWT_SECRET=your_jwt_secret_minimum_32_chars
ALLOWED_ORIGINS=http://localhost:3001
```

### Q: How do I verify my installation is working?
**A:**
```bash
# Check service health
curl http://localhost:8000/health      # Orchestrator
curl http://localhost:3001             # Console
curl http://localhost:8787/health      # Terminal Daemon

# Check database connectivity
curl http://localhost:8000/healthz     # DB health check
```

## ⚙️ Configuration

### Q: How do I configure CORS for my domain?
**A:** Update the `BACKEND_CORS_ORIGINS` in your orchestrator `.env` file:
```env
BACKEND_CORS_ORIGINS=["http://localhost:3001", "https://your-domain.com"]
```

### Q: How do I change the default ports?
**A:** Update the respective environment variables:
- Orchestrator: `PORT=8000`
- Console: `PORT=3001` (Next.js default)
- Terminal Daemon: `PORT=8787`

### Q: How do I configure JWT token expiration?
**A:** Set `ACCESS_TOKEN_EXPIRE_MINUTES` in the orchestrator configuration:
```env
ACCESS_TOKEN_EXPIRE_MINUTES=30  # 30 minutes default
```

### Q: How do I enable/disable security features?
**A:** Configure security settings in the orchestrator:
```env
ENVIRONMENT=production  # Enables HTTPS enforcement
CSRF_ENABLED=true      # Enable CSRF protection
RATE_LIMITING=true     # Enable rate limiting
```

## 💻 Development

### Q: How do I run tests?
**A:**
```bash
# Run all tests
python3 scripts/pr_gate.py --run-tests

# Run specific service tests
cd services/orchestrator && python -m pytest
cd services/console && npm test
cd services/terminal-daemon && npm test
```

### Q: How do I lint my code?
**A:**
```bash
# Python linting
ruff check services/orchestrator
ruff check --fix services/orchestrator  # Auto-fix

# Frontend linting
cd services/console && npm run lint
cd services/console && npm run lint:fix  # Auto-fix
```

### Q: How do I run database migrations?
**A:**
```bash
cd services/orchestrator

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Rollback migration
alembic downgrade -1
```

### Q: How do I debug issues during development?
**A:**
1. Check service logs:
   ```bash
   docker compose logs -f [service-name]
   ```
2. Enable debug mode in environment variables:
   ```env
   LOG_LEVEL=DEBUG
   ENABLE_DEBUG_MODE=true
   ```
3. Use browser developer tools for frontend issues
4. Check database connectivity and logs

## 🔗 API Usage

### Q: How do I authenticate with the API?
**A:**
```bash
# 1. Login to get access token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# 2. Use token in subsequent requests
curl -X GET http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer your_access_token"
```

### Q: Where can I find the API documentation?
**A:** 
- Interactive docs: http://localhost:8000/docs
- ReDoc format: http://localhost:8000/redoc
- OpenAPI schema: http://localhost:8000/api/v1/openapi.json
- Written docs: [API Documentation](../api/README.md)

### Q: How do I handle API rate limiting?
**A:** The API implements rate limiting. If you hit limits:
1. Implement exponential backoff in your client
2. Use authenticated requests (higher limits for authenticated users)
3. Configure rate limits in environment variables if needed

### Q: What data formats does the API accept?
**A:** The API primarily accepts and returns JSON. All endpoints expecting data require:
```bash
-H "Content-Type: application/json"
```

## 🛡️ Security

### Q: How do I secure my Kyros Praxis installation?
**A:**
1. **Use strong secrets:** Generate secure random strings for all secret keys
2. **Enable HTTPS:** Set `ENVIRONMENT=production` to enforce HTTPS
3. **Configure CORS:** Restrict origins to your specific domains
4. **Use environment variables:** Never commit secrets to version control
5. **Regular updates:** Keep dependencies up to date

### Q: How do I rotate JWT secrets?
**A:**
1. Generate new secret: `openssl rand -base64 32`
2. Update JWT_SECRET in all service configurations
3. Restart all services
4. Note: This will invalidate all existing tokens

### Q: How do I add new users?
**A:**
```bash
# Via API (requires admin token)
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "username": "newuser",
    "email": "user@example.com", 
    "password": "secure_password",
    "role": "user"
  }'
```

### Q: How do I configure role-based access control?
**A:** User roles are managed through the API. Available roles:
- `admin` - Full system access
- `user` - Standard user access
- `readonly` - Read-only access

## ⚡ Performance

### Q: How do I optimize database performance?
**A:**
1. **Connection pooling:** Configure `DATABASE_POOL_SIZE` environment variable
2. **Indexing:** Ensure proper database indexes are in place
3. **Monitoring:** Use the `/api/v1/monitoring/metrics` endpoint
4. **Regular maintenance:** Run database optimization queries

### Q: How do I scale the services?
**A:**
1. **Horizontal scaling:** Run multiple instances behind a load balancer
2. **Database scaling:** Use read replicas for read-heavy workloads
3. **Caching:** Configure Redis for session and data caching
4. **Resource limits:** Configure appropriate memory and CPU limits

### Q: How do I monitor system performance?
**A:**
```bash
# Get system metrics
curl -X GET http://localhost:8000/api/v1/monitoring/metrics \
  -H "Authorization: Bearer $TOKEN"

# Monitor service health
curl -X GET http://localhost:8000/api/v1/monitoring/health \
  -H "Authorization: Bearer $TOKEN"
```

## 🔧 Troubleshooting

### Q: Services won't start - what should I check?
**A:**
1. **Docker:** Ensure Docker is running: `docker info`
2. **Ports:** Check if ports are available: `netstat -tulpn | grep :8000`
3. **Environment:** Verify `.env` files are configured correctly
4. **Logs:** Check service logs: `docker compose logs -f`
5. **Database:** Ensure PostgreSQL is accessible

### Q: I'm getting CORS errors - how do I fix them?
**A:**
1. Add your domain to `BACKEND_CORS_ORIGINS`:
   ```env
   BACKEND_CORS_ORIGINS=["http://localhost:3001", "https://your-domain.com"]
   ```
2. Restart the orchestrator service
3. Clear browser cache and try again

### Q: Authentication is failing - what could be wrong?
**A:**
1. **JWT Secret:** Ensure JWT_SECRET is the same across all services
2. **Token expiration:** Check if your token has expired
3. **CORS:** Verify CORS is configured for your domain
4. **Environment:** Ensure ENVIRONMENT variable matches your setup

### Q: Database connection is failing - how do I fix it?
**A:**
1. **Check connection string:** Verify DATABASE_URL format:
   ```
   postgresql://username:password@host:port/database
   ```
2. **Database running:** Ensure PostgreSQL container is running:
   ```bash
   docker compose ps postgres
   ```
3. **Network access:** Check if database port is accessible
4. **Migrations:** Run database migrations:
   ```bash
   cd services/orchestrator && alembic upgrade head
   ```

### Q: Terminal sessions aren't working - what's wrong?
**A:**
1. **WebSocket connection:** Check browser console for WebSocket errors
2. **Authentication:** Ensure JWT token is valid and not expired
3. **CORS:** Verify WebSocket CORS configuration in Terminal Daemon
4. **Firewall:** Check if port 8787 is accessible

### Q: How do I get more detailed error information?
**A:**
1. **Enable debug logging:**
   ```env
   LOG_LEVEL=DEBUG
   ```
2. **Check service logs:**
   ```bash
   docker compose logs -f [service-name]
   ```
3. **Browser console:** Check browser developer tools for frontend errors
4. **API responses:** Look for detailed error messages in API responses

### Q: Performance is slow - how can I improve it?
**A:**
1. **Resource allocation:** Increase Docker container resources
2. **Database tuning:** Optimize PostgreSQL configuration
3. **Caching:** Enable Redis caching
4. **Network:** Check network latency between services
5. **Monitoring:** Use performance monitoring endpoints to identify bottlenecks

## 🔗 Additional Resources

- [User Guide](../user-guide/README.md) - Comprehensive usage guide
- [Troubleshooting Guide](../troubleshooting/) - Detailed troubleshooting steps
- [API Documentation](../api/README.md) - Complete API reference
- [Architecture Overview](../architecture/overview.md) - System design details
- [Security Guidelines](../security/README.md) - Security best practices
- [Operations Manual](../ops/runbooks/README.md) - Deployment and operations

## 💬 Getting Help

If you can't find the answer to your question here:

1. Check the [Troubleshooting Guide](../troubleshooting/) for detailed solutions
2. Search existing [GitHub Issues](https://github.com/tdawe1/kyros-praxis/issues)
3. Create a new issue with:
   - Detailed description of the problem
   - Steps to reproduce
   - Error messages and logs
   - System information (OS, Docker version, etc.)
   - Configuration details (sanitized, no secrets)