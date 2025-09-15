# Railway Services Configuration

## Services

### 1. FastAPI Orchestrator
- **Name**: kyros-praxis-api
- **Source**: services/orchestrator
- **Build Command**: pip install -r requirements.txt
- **Start Command**: uvicorn main:app --host 0.0.0.0 --port 8000
- **Environment**: 
  - Production: api.kyros-praxis.com
  - Preview: api-${PR_NUMBER}.kyros-praxis.railway.app

### 2. Terminal Daemon
- **Name**: kyros-praxis-daemon
- **Source**: services/terminal-daemon
- **Build Command**: npm install && npm run build
- **Start Command**: npm start
- **Port**: 8787
- **Environment**:
  - Production: daemon.kyros-praxis.com
  - Preview: daemon-${PR_NUMBER}.kyros-praxis.railway.app

### 3. PostgreSQL Database
- **Name**: kyros-praxis-db
- **Plugin**: PostgreSQL
- **Version**: 15
- **Environment**: Shared across preview and production

### 4. Qdrant Vector Database
- **Name**: kyros-praxis-qdrant
- **Plugin**: Qdrant
- **Version**: latest
- **Environment**: Shared across preview and production

## Variables

### Production Environment
```
DATABASE_URL=postgresql://user:password@kyros-praxis-db:5432/kyros_prod
QDRANT_URL=http://kyros-praxis-qdrant:6333
QDRANT_API_KEY=your_qdrant_api_key
JWT_SECRET=your_jwt_secret
REDIS_URL=redis://your_redis_url
SENTRY_DSN=your_sentry_dsn
OTEL_EXPORTER_OTLP_ENDPOINT=your_otlp_endpoint
```

### Preview Environment (per PR)
```
DATABASE_URL=postgresql://user:password@kyros-praxis-db:5432/kyros_pr_${PR_NUMBER}
QDRANT_URL=http://kyros-praxis-qdrant:6333
QDRANT_API_KEY=your_qdrant_api_key
JWT_SECRET=preview_jwt_secret
REDIS_URL=redis://your_redis_url
SENTRY_DSN=your_preview_sentry_dsn
OTEL_EXPORTER_OTLP_ENDPOINT=your_otlp_endpoint
```

## Health Checks

### FastAPI Health Check
- **URL**: `/api/v1/utils/health-check`
- **Method**: GET
- **Expected**: HTTP 200 with JSON response

### Terminal Daemon Health Check
- **URL**: `/health`
- **Method**: GET
- **Expected**: HTTP 200 with JSON response

## Deployment Hooks

### Pre-deploy (Database Migrations)
```bash
# Run Alembic migrations
python -m alembic upgrade head
```

### Post-deploy (Health Check)
```bash
# Wait for service to be ready
sleep 10
curl -f http://localhost:8000/api/v1/utils/health-check
```