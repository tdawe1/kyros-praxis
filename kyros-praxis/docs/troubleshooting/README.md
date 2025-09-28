# Troubleshooting Guide

This guide provides step-by-step troubleshooting procedures for common issues with Kyros Praxis.

## 📚 Table of Contents

- [General Diagnostics](#general-diagnostics)
- [Service Startup Issues](#service-startup-issues)
- [Database Connection Problems](#database-connection-problems)
- [Authentication Issues](#authentication-issues)
- [API Connection Problems](#api-connection-problems)
- [Terminal Session Issues](#terminal-session-issues)
- [Performance Problems](#performance-problems)
- [Security-Related Issues](#security-related-issues)
- [Development Environment Issues](#development-environment-issues)

## 🔍 General Diagnostics

Before diving into specific issues, run these general diagnostic commands:

### System Health Check
```bash
# Check Docker status
docker info
docker compose ps

# Check service health endpoints
curl -f http://localhost:8000/health || echo "Orchestrator unhealthy"
curl -f http://localhost:3001 || echo "Console unreachable"
curl -f http://localhost:8787/health || echo "Terminal Daemon unhealthy"
curl -f http://localhost:8000/healthz || echo "Database connection failed"
```

### Log Collection
```bash
# Collect all service logs
docker compose logs --timestamps > kyros-debug-logs.txt

# Get specific service logs
docker compose logs -f orchestrator
docker compose logs -f console
docker compose logs -f terminal-daemon
docker compose logs -f postgres
```

### Resource Usage
```bash
# Check resource usage
docker stats

# Check disk space
df -h

# Check memory usage
free -h
```

## 🚀 Service Startup Issues

### Problem: Services won't start
**Symptoms:**
- `docker compose up` fails
- Services exit immediately after starting
- Port binding errors

**Diagnostic Steps:**
1. **Check port availability:**
   ```bash
   # Check if ports are in use
   netstat -tulpn | grep -E ':(3001|8000|8787|5432|6379)'
   
   # On macOS, use lsof instead
   lsof -i :8000
   ```

2. **Check Docker resources:**
   ```bash
   docker system df
   docker system prune  # Clean up if needed
   ```

3. **Verify environment configuration:**
   ```bash
   # Check if .env files exist
   ls -la services/*/.env
   
   # Validate environment file syntax
   grep -n "=" services/orchestrator/.env
   ```

**Solutions:**
- **Port conflicts:** Change ports in docker-compose.yml or stop conflicting services
- **Resource limits:** Increase Docker memory/CPU limits in Docker Desktop
- **Permission issues:** Ensure user has Docker permissions: `sudo usermod -aG docker $USER`
- **Missing .env files:** Copy from .env.example files

### Problem: Container keeps restarting
**Symptoms:**
- Container status shows "Restarting"
- Services appear to start then immediately crash

**Diagnostic Steps:**
```bash
# Check container exit codes
docker compose ps -a

# Get detailed logs
docker compose logs --tail=50 [service-name]

# Check container resource limits
docker stats --no-stream
```

**Solutions:**
1. **Check application logs for specific error messages**
2. **Verify environment variables are correct**
3. **Ensure database is accessible before starting dependent services**
4. **Check for missing dependencies or files**

## 🗄️ Database Connection Problems

### Problem: Database connection refused
**Symptoms:**
- "Connection refused" errors in orchestrator logs
- `/healthz` endpoint returns 500 error
- Database-related operations fail

**Diagnostic Steps:**
```bash
# Check if PostgreSQL container is running
docker compose ps postgres

# Test database connectivity directly
docker compose exec postgres psql -U kyros -d kyros_db -c "SELECT 1;"

# Check database logs
docker compose logs postgres

# Verify connection string format
echo $DATABASE_URL
```

**Solutions:**
1. **Ensure PostgreSQL container is running:**
   ```bash
   docker compose up -d postgres
   ```

2. **Check connection string format:**
   ```env
   DATABASE_URL=postgresql://username:password@host:port/database
   ```

3. **Verify database credentials:**
   ```bash
   # Connect manually to test credentials
   docker compose exec postgres psql -U kyros -d kyros_db
   ```

4. **Reset database if corrupted:**
   ```bash
   docker compose down
   docker volume rm kyros-praxis_postgres_data
   docker compose up -d postgres
   cd services/orchestrator && alembic upgrade head
   ```

### Problem: Migration failures
**Symptoms:**
- Alembic migration errors
- Database schema out of sync
- "Table doesn't exist" errors

**Diagnostic Steps:**
```bash
cd services/orchestrator

# Check current migration status
alembic current

# Check migration history
alembic history

# Verify database tables
docker compose exec postgres psql -U kyros -d kyros_db -c "\dt"
```

**Solutions:**
1. **Run pending migrations:**
   ```bash
   alembic upgrade head
   ```

2. **Reset migrations if corrupted:**
   ```bash
   # Backup data first if needed
   docker compose exec postgres pg_dump -U kyros kyros_db > backup.sql
   
   # Drop and recreate database
   docker compose exec postgres psql -U kyros -c "DROP DATABASE kyros_db;"
   docker compose exec postgres psql -U kyros -c "CREATE DATABASE kyros_db;"
   
   # Run migrations from scratch
   alembic upgrade head
   ```

3. **Fix migration conflicts:**
   ```bash
   # If multiple migration branches exist
   alembic merge -m "merge migrations" heads
   alembic upgrade head
   ```

## 🔐 Authentication Issues

### Problem: Login fails with correct credentials
**Symptoms:**
- Login returns 401 Unauthorized
- "Incorrect username or password" error
- Token not generated

**Diagnostic Steps:**
```bash
# Check if default user exists
docker compose exec postgres psql -U kyros -d kyros_db -c "SELECT * FROM users;"

# Test login endpoint directly
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}' \
  -v
```

**Solutions:**
1. **Create default user if missing:**
   ```bash
   # Connect to database and create user
   docker compose exec postgres psql -U kyros -d kyros_db
   
   # In psql prompt:
   INSERT INTO users (username, email, hashed_password, is_active) 
   VALUES ('admin', 'admin@example.com', '$2b$12$hashed_password', true);
   ```

2. **Reset user password:**
   ```python
   # In Python (services/orchestrator directory)
   from passlib.context import CryptContext
   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
   hashed = pwd_context.hash("your_new_password")
   print(hashed)
   ```

3. **Check JWT configuration:**
   ```bash
   # Ensure JWT_SECRET is set and consistent across services
   grep JWT_SECRET services/*/env
   ```

### Problem: Token validation fails
**Symptoms:**
- "Invalid token" errors
- Token expired messages
- 401 errors on authenticated endpoints

**Diagnostic Steps:**
```bash
# Check token expiration settings
grep TOKEN_EXPIRE services/orchestrator/.env

# Decode JWT token (use jwt.io or jwt-cli)
# Check issued time, expiration, and signature
```

**Solutions:**
1. **Ensure JWT secrets match across services:**
   ```bash
   # Check all JWT_SECRET values are identical
   grep -H JWT_SECRET services/*/.env
   ```

2. **Check token expiration:**
   ```env
   ACCESS_TOKEN_EXPIRE_MINUTES=30  # Adjust as needed
   ```

3. **Verify system time synchronization:**
   ```bash
   # Ensure system time is correct
   date
   ntpq -p  # Check NTP sync if available
   ```

## 🔗 API Connection Problems

### Problem: CORS errors in browser
**Symptoms:**
- "CORS policy" errors in browser console
- Preflight request failures
- Cross-origin request blocked

**Diagnostic Steps:**
```bash
# Check CORS configuration
grep CORS services/orchestrator/.env

# Test CORS with curl
curl -H "Origin: http://localhost:3001" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Authorization" \
     -X OPTIONS \
     http://localhost:8000/api/v1/jobs -v
```

**Solutions:**
1. **Update CORS origins:**
   ```env
   BACKEND_CORS_ORIGINS=["http://localhost:3001", "https://your-domain.com"]
   ```

2. **Allow all origins for development (NOT for production):**
   ```env
   BACKEND_CORS_ORIGINS=["*"]
   ```

3. **Restart orchestrator service after CORS changes:**
   ```bash
   docker compose restart orchestrator
   ```

### Problem: API endpoints return 404
**Symptoms:**
- All API calls return 404 Not Found
- Swagger UI not accessible
- Base URL returns empty response

**Diagnostic Steps:**
```bash
# Check orchestrator service logs
docker compose logs orchestrator

# Test base endpoints
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/docs

# Check FastAPI configuration
grep -A5 -B5 "FastAPI" services/orchestrator/main.py
```

**Solutions:**
1. **Verify service is running on correct port:**
   ```bash
   docker compose ps
   netstat -tulpn | grep 8000
   ```

2. **Check FastAPI app initialization:**
   - Ensure all routers are properly included
   - Verify API prefix configuration
   - Check for import errors in logs

3. **Restart orchestrator service:**
   ```bash
   docker compose restart orchestrator
   ```

## 💻 Terminal Session Issues

### Problem: WebSocket connection fails
**Symptoms:**
- Terminal interface shows connection error
- WebSocket connection refused
- No terminal output

**Diagnostic Steps:**
```bash
# Check terminal daemon logs
docker compose logs terminal-daemon

# Test WebSocket connection
wscat -c ws://localhost:8787  # Install wscat: npm install -g wscat

# Check if terminal daemon is listening
netstat -tulpn | grep 8787
```

**Solutions:**
1. **Verify terminal daemon is running:**
   ```bash
   docker compose ps terminal-daemon
   curl http://localhost:8787/health
   ```

2. **Check JWT authentication for WebSocket:**
   ```javascript
   // Ensure token is passed correctly
   const ws = new WebSocket('ws://localhost:8787?token=your_jwt_token');
   ```

3. **Verify CORS configuration for WebSocket:**
   ```env
   # In terminal-daemon .env
   ALLOWED_ORIGINS=http://localhost:3001
   ```

### Problem: Terminal commands don't execute
**Symptoms:**
- Commands sent but no response
- Terminal session appears frozen
- Process hangs indefinitely

**Diagnostic Steps:**
```bash
# Check terminal daemon resource usage
docker compose exec terminal-daemon ps aux

# Check for stuck processes
docker compose exec terminal-daemon pgrep -f pty

# Monitor terminal daemon logs in real-time
docker compose logs -f terminal-daemon
```

**Solutions:**
1. **Restart terminal daemon:**
   ```bash
   docker compose restart terminal-daemon
   ```

2. **Check resource limits:**
   ```env
   # In terminal-daemon .env
   MAX_SESSIONS=100
   SESSION_TIMEOUT=3600
   MAX_COMMAND_LENGTH=10000
   ```

3. **Kill stuck sessions:**
   ```bash
   docker compose exec terminal-daemon pkill -f pty
   docker compose restart terminal-daemon
   ```

## ⚡ Performance Problems

### Problem: Slow API responses
**Symptoms:**
- API requests take >5 seconds
- Timeouts on complex operations
- High CPU/memory usage

**Diagnostic Steps:**
```bash
# Monitor resource usage
docker stats --no-stream

# Check database performance
docker compose exec postgres pg_stat_activity

# Test API response times
time curl http://localhost:8000/api/v1/jobs

# Check for long-running queries
docker compose exec postgres psql -U kyros -d kyros_db -c "
  SELECT query, state, query_start 
  FROM pg_stat_activity 
  WHERE state = 'active' AND query_start < now() - interval '5 seconds';
"
```

**Solutions:**
1. **Increase resource limits:**
   ```yaml
   # In docker-compose.yml
   services:
     orchestrator:
       deploy:
         resources:
           limits:
             memory: 1G
             cpus: '1.0'
   ```

2. **Optimize database queries:**
   ```sql
   -- Add missing indexes
   CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
   CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);
   ```

3. **Enable database connection pooling:**
   ```env
   DATABASE_POOL_SIZE=20
   DATABASE_MAX_OVERFLOW=10
   ```

4. **Monitor and identify bottlenecks:**
   ```bash
   # Use monitoring endpoint
   curl http://localhost:8000/api/v1/monitoring/metrics
   ```

### Problem: High memory usage
**Symptoms:**
- Containers using excessive memory
- Out of memory errors
- System becomes unresponsive

**Diagnostic Steps:**
```bash
# Check memory usage by service
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Check system memory
free -h

# Monitor PostgreSQL memory
docker compose exec postgres psql -U kyros -d kyros_db -c "
  SELECT name, setting, unit FROM pg_settings 
  WHERE name IN ('shared_buffers', 'work_mem', 'maintenance_work_mem');
"
```

**Solutions:**
1. **Set memory limits:**
   ```yaml
   # In docker-compose.yml
   services:
     postgres:
       deploy:
         resources:
           limits:
             memory: 2G
   ```

2. **Optimize PostgreSQL configuration:**
   ```env
   # Add to postgres environment
   POSTGRES_SHARED_BUFFERS=256MB
   POSTGRES_WORK_MEM=4MB
   ```

3. **Clean up unused Docker resources:**
   ```bash
   docker system prune -a
   docker volume prune
   ```

## 🛡️ Security-Related Issues

### Problem: HTTPS redirect not working
**Symptoms:**
- HTTP requests not redirected to HTTPS
- Mixed content warnings
- Insecure connection warnings

**Diagnostic Steps:**
```bash
# Check environment configuration
grep ENVIRONMENT services/orchestrator/.env
grep HTTPS services/orchestrator/.env

# Test HTTPS redirect
curl -I http://localhost:8000/ -L
```

**Solutions:**
1. **Enable production environment:**
   ```env
   ENVIRONMENT=production
   FORCE_HTTPS=true
   ```

2. **Configure reverse proxy for HTTPS:**
   ```nginx
   # Nginx configuration example
   server {
       listen 80;
       return 301 https://$server_name$request_uri;
   }
   
   server {
       listen 443 ssl;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       location / {
           proxy_pass http://localhost:8000;
       }
   }
   ```

### Problem: Rate limiting too aggressive
**Symptoms:**
- "Too Many Requests" errors
- Users blocked unexpectedly
- API calls failing frequently

**Diagnostic Steps:**
```bash
# Check rate limiting configuration
grep -i rate services/orchestrator/.env

# Test rate limits
for i in {1..20}; do
  curl -o /dev/null -s -w "%{http_code}\n" http://localhost:8000/health
done
```

**Solutions:**
1. **Adjust rate limits:**
   ```env
   # Configure rate limiting (if available)
   RATE_LIMIT_PER_MINUTE=60
   RATE_LIMIT_BURST=10
   ```

2. **Whitelist trusted IPs:**
   ```env
   RATE_LIMIT_WHITELIST=["127.0.0.1", "your.trusted.ip"]
   ```

3. **Disable rate limiting for development:**
   ```env
   ENVIRONMENT=development  # Usually disables rate limiting
   ```

## 🔧 Development Environment Issues

### Problem: Hot reloading not working
**Symptoms:**
- Changes to code don't reflect automatically
- Need to restart services manually for changes
- Development server doesn't detect file changes

**Diagnostic Steps:**
```bash
# Check if volumes are mounted correctly
docker compose config | grep -A5 volumes

# Verify file permissions
ls -la services/orchestrator/
ls -la services/console/

# Check if processes are running with correct flags
docker compose exec orchestrator ps aux | grep uvicorn
docker compose exec console ps aux | grep node
```

**Solutions:**
1. **For FastAPI (orchestrator):**
   ```bash
   # Ensure --reload flag is used
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **For Next.js (console):**
   ```bash
   # Ensure dev mode is used
   npm run dev
   ```

3. **Check volume mounts in docker-compose.yml:**
   ```yaml
   services:
     orchestrator:
       volumes:
         - ./services/orchestrator:/app
     console:
       volumes:
         - ./services/console:/app
   ```

### Problem: Package installation failures
**Symptoms:**
- npm install fails
- pip install fails
- Missing dependency errors

**Diagnostic Steps:**
```bash
# Check Node.js/npm versions
node --version
npm --version

# Check Python/pip versions
python --version
pip --version

# Check package.json/requirements.txt syntax
cat services/console/package.json | jq .
cat services/orchestrator/requirements.txt
```

**Solutions:**
1. **Clear package manager caches:**
   ```bash
   # npm
   npm cache clean --force
   rm -rf node_modules package-lock.json
   npm install
   
   # pip
   pip cache purge
   pip install --no-cache-dir -r requirements.txt
   ```

2. **Use specific package versions:**
   ```bash
   # If installation fails, try specific versions
   npm install package-name@specific-version
   pip install package-name==specific-version
   ```

3. **Check network connectivity:**
   ```bash
   # Test registry access
   curl -I https://registry.npmjs.org/
   curl -I https://pypi.org/
   ```

## 📞 Getting Additional Help

If these troubleshooting steps don't resolve your issue:

1. **Collect detailed information:**
   ```bash
   # System information
   uname -a
   docker --version
   docker compose version
   
   # Service logs
   docker compose logs --timestamps > debug-logs.txt
   
   # Configuration (sanitize secrets!)
   cat services/orchestrator/.env.example
   ```

2. **Check GitHub issues:**
   - Search existing issues: https://github.com/tdawe1/kyros-praxis/issues
   - Look for similar problems and solutions

3. **Create a new issue with:**
   - Detailed problem description
   - Steps to reproduce
   - System information
   - Error messages and logs
   - Configuration details (without secrets)

## 🔗 Additional Resources

- [FAQ](../faq/README.md) - Frequently asked questions
- [User Guide](../user-guide/README.md) - Comprehensive usage guide
- [API Documentation](../api/README.md) - Complete API reference
- [Security Guidelines](../security/README.md) - Security best practices
- [Operations Manual](../ops/runbooks/README.md) - Deployment and operations