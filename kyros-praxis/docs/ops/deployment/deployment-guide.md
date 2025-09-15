# Deployment Guide

This guide provides comprehensive procedures for deploying the Kyros Praxis platform across different environments, from development to production.

## 🎯 Deployment Targets

### Environment Types

| Environment | Purpose | Access Level | Auto-deploy | Backup Frequency |
|-------------|---------|--------------|-------------|------------------|
| **Development** | Local development & testing | Full access | Manual | None |
| **Staging** | Pre-production testing | Restricted | Automatic | Daily |
| **Production** | Live customer-facing service | Production only | Manual | Hourly |

### Infrastructure Requirements

#### Minimum Requirements
- **CPU**: 4 cores per service
- **Memory**: 8GB RAM per service
- **Storage**: 50GB SSD per service
- **Network**: 1Gbps bandwidth
- **Database**: PostgreSQL 14+
- **Cache**: Redis 6+

#### Recommended Production Requirements
- **CPU**: 8+ cores per service
- **Memory**: 16GB+ RAM per service
- **Storage**: 100GB+ SSD with encryption
- **Network**: 10Gbps bandwidth
- **Load Balancing**: Multiple instances
- **Monitoring**: Full observability stack

## 🚀 Deployment Methods

### 1. Docker Compose (Development/Small Production)

#### Prerequisites
- Docker and Docker Compose installed
- Environment variables configured
- SSL certificates (for production)

#### Quick Start
```bash
# Clone repository
git clone https://github.com/your-org/kyros-praxis.git
cd kyros-praxis

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker-compose up -d

# Verify deployment
docker-compose ps
docker-compose logs
```

#### Production Configuration
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  console:
    image: kyros/console:latest
    ports:
      - "443:3001"
    environment:
      - NODE_ENV=production
      - NEXTAUTH_URL=https://your-domain.com
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
    volumes:
      - ./ssl:/etc/ssl/certs
    depends_on:
      - orchestrator
      - redis

  orchestrator:
    image: kyros/orchestrator:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - postgres
      - redis

  terminal-daemon:
    image: kyros/terminal-daemon:latest
    ports:
      - "8787:8787"
    environment:
      - JWT_SECRET=${JWT_SECRET}
      - NODE_ENV=production

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=kyros
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 2. Kubernetes (Production/Enterprise)

#### Cluster Setup
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: kyros-praxis
---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kyros-config
  namespace: kyros-praxis
data:
  NODE_ENV: "production"
  LOG_LEVEL: "info"
  DATABASE_URL: "postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/kyros"
  REDIS_URL: "redis://redis:6379"
```

#### Secrets Management
```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: kyros-secrets
  namespace: kyros-praxis
type: Opaque
data:
  # Values must be base64 encoded
  nextauth-secret: <base64-encoded-secret>
  jwt-secret: <base64-encoded-secret>
  database-password: <base64-encoded-password>
```

#### Deployment Manifests
```yaml
# k8s/console-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: console
  namespace: kyros-praxis
spec:
  replicas: 3
  selector:
    matchLabels:
      app: console
  template:
    metadata:
      labels:
        app: console
    spec:
      containers:
      - name: console
        image: kyros/console:latest
        ports:
        - containerPort: 3001
        env:
        - name: NODE_ENV
          valueFrom:
            configMapKeyRef:
              name: kyros-config
              key: NODE_ENV
        - name: NEXTAUTH_SECRET
          valueFrom:
            secretKeyRef:
              name: kyros-secrets
              key: nextauth-secret
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 3001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 3001
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: console-service
  namespace: kyros-praxis
spec:
  selector:
    app: console
  ports:
  - port: 80
    targetPort: 3001
  type: ClusterIP
```

#### Ingress Configuration
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: kyros-ingress
  namespace: kyros-praxis
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: kyros-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: console-service
            port:
              number: 80
```

### 3. Cloud Provider Deployment (AWS/GCP/Azure)

#### AWS ECS Deployment
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker build -t kyros/console .
docker tag kyros/console:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/kyros-console:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/kyros-console:latest

# Deploy to ECS
aws ecs update-service --cluster kyros-cluster --service console-service --force-new-deployment
```

#### GCP Cloud Run Deployment
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/kyros-console
gcloud run deploy --image gcr.io/PROJECT-ID/kyros-console --platform managed
```

## 🔧 Configuration Management

### Environment Variables

#### Required Variables
```bash
# Application
NODE_ENV=production
PORT=3001

# Security
NEXTAUTH_SECRET=your_secure_secret_minimum_32_chars
JWT_SECRET=your_jwt_secret_minimum_32_chars
SECRET_KEY=your_database_secret_minimum_32_chars

# Database
DATABASE_URL=postgresql://user:password@host:5432/kyros
POSTGRES_DB=kyros
POSTGRES_USER=kyros_user
POSTGRES_PASSWORD=your_secure_password

# Redis
REDIS_URL=redis://host:6379

# Services
ORCHESTRATOR_URL=http://orchestrator:8000
TERMINAL_DAEMON_URL=ws://terminal-daemon:8787
SERVICE_REGISTRY_URL=http://service-registry:8001

# CORS
ALLOWED_ORIGINS=https://your-domain.com
```

#### Optional Variables
```bash
# Logging
LOG_LEVEL=info
STRUCTURED_LOGGING=true

# Performance
CACHE_TTL=300
RATE_LIMIT_REQUESTS=100
MAX_CONNECTIONS=100

# Security
CORS_MAX_AGE=86400
JWT_EXPIRATION=1800
CSRF_ENABLED=true

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

### Configuration Files

#### Database Configuration
```python
# config/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

DATABASE_URL = os.getenv('DATABASE_URL')

# Production pool configuration
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

#### Redis Configuration
```python
# config/redis.py
import redis
import os

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD'),
    decode_responses=True,
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True
)
```

## 🔄 CI/CD Pipeline Integration

### GitHub Actions Example
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        npm ci
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        npm test
        pytest

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker images
      run: |
        docker-compose -f docker-compose.prod.yml build
    
    - name: Deploy to production
      run: |
        docker-compose -f docker-compose.prod.yml up -d
```

### GitLab CI Example
```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

test:
  stage: test
  script:
    - npm ci
    - pip install -r requirements.txt
    - npm test
    - pytest

build:
  stage: build
  script:
    - docker-compose build
  only:
    - main

deploy:
  stage: deploy
  script:
    - docker-compose -f docker-compose.prod.yml up -d
  only:
    - main
  when: manual
```

## 🛡️ Security Considerations

### Network Security
- **Firewall Rules**: Restrict access to necessary ports only
- **VPN Access**: Require VPN for administrative access
- **Network Segmentation**: Separate web, application, and database tiers
- **SSL/TLS**: Encrypt all network communications

### Container Security
- **Non-root Users**: Run containers as non-root users
- **Read-only Filesystems**: Where possible
- **Resource Limits**: Set CPU and memory limits
- **Image Scanning**: Regular vulnerability scanning

### Data Security
- **Encryption at Rest**: Enable database encryption
- **Backup Encryption**: Encrypt backup files
- **Secrets Management**: Use proper secrets management
- **Audit Logging**: Log all access and modifications

## 📊 Monitoring & Health Checks

### Health Check Endpoints
```
GET /health         - Basic health check
GET /healthz        - Health check with dependencies
GET /readyz         - Readiness check
GET /metrics        - Application metrics
```

### Monitoring Stack Recommendations
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- **Loki**: Log aggregation
- **Alertmanager**: Alert management
- **Jaeger**: Distributed tracing

### Critical Metrics to Monitor
- Service availability and uptime
- Request latency and error rates
- Database connection pool usage
- Memory and CPU utilization
- WebSocket connection counts
- Authentication success/failure rates

## 🔄 Rollback Procedures

### Manual Rollback
```bash
# View previous deployments
docker images | grep kyros

# Rollback to specific version
docker-compose -f docker-compose.prod.yml up -d --no-deps console:kyros/console:previous-version

# Kubernetes rollback
kubectl rollout undo deployment/console -n kyros-praxis
```

### Automated Rollback Triggers
- Health check failures > 5 minutes
- Error rate > 10% for 5 minutes
- Critical service dependencies unavailable

## 📋 Deployment Checklist

### Pre-deployment
- [ ] Backup current database
- [ ] Review deployment scripts
- [ ] Verify environment configuration
- [ ] Test rollback procedures
- [ ] Notify stakeholders of maintenance window

### During Deployment
- [ ] Monitor health checks
- [ ] Check error rates
- [ ] Verify service connectivity
- [ ] Monitor resource usage
- [ ] Test critical functionality

### Post-deployment
- [ ] Run smoke tests
- [ ] Verify all services healthy
- [ ] Check monitoring alerts
- [ ] Update runbooks if needed
- [ ] Document deployment results

## 🔧 Troubleshooting

### Common Issues

**Service Won't Start**
```bash
# Check logs
docker-compose logs [service-name]

# Check resource usage
docker stats

# Verify environment variables
docker-compose config
```

**Database Connection Issues**
```bash
# Test database connectivity
docker exec postgres pg_isready

# Check database logs
docker-compose logs postgres

# Verify connection string
echo $DATABASE_URL
```

**Network Connectivity Issues**
```bash
# Test service connectivity
docker exec console curl -f http://orchestrator:8000/health

# Check network configuration
docker network ls
docker network inspect kyros_default
```

### Performance Issues
```bash
# Monitor resource usage
docker stats

# Check database performance
docker exec postgres psql -c "SELECT * FROM pg_stat_activity;"

# Analyze logs for errors
docker-compose logs --tail=100
```

## 📚 Additional Resources

- [Architecture Overview](../../architecture/overview.md)
- [Security Guidelines](../../security/README.md)
- [API Documentation](../../api/README.md)
- [Service Documentation](../../../services/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Monitoring Best Practices](../monitoring/setup.md)