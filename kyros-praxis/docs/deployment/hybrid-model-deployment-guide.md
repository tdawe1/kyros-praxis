# Kyros Hybrid Model System - Deployment Guide

## Table of Contents
- [Deployment Overview](#deployment-overview)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Local Development Deployment](#local-development-deployment)
- [Production Deployment](#production-deployment)
- [Cloud Deployment](#cloud-deployment)
- [High Availability Deployment](#high-availability-deployment)
- [Configuration Management](#configuration-management)
- [Database Setup](#database-setup)
- [Security Configuration](#security-configuration)
- [Monitoring Setup](#monitoring-setup)
- [Backup and Recovery](#backup-and-recovery)
- [Migration Guide](#migration-guide)
- [Troubleshooting Deployment](#troubleshooting-deployment)

## Deployment Overview

### Deployment Architectures

**Development/Testing:**
- Single-node deployment
- Docker Compose orchestration
- Local database and cache
- Minimal resource requirements

**Staging:**
- Multi-node deployment
- Kubernetes orchestration
- Production-like database
- Full monitoring stack

**Production:**
- Multi-region deployment
- Kubernetes with auto-scaling
- Managed database services
- Comprehensive monitoring and alerting

### Deployment Components

**Core Services:**
- Console (Next.js frontend)
- Orchestrator (FastAPI backend)
- Terminal Daemon (Node.js WebSocket service)
- MCP Servers (AI model integration)

**Infrastructure:**
- PostgreSQL database
- Redis cache
- Load balancers
- Monitoring stack (Prometheus, Grafana)
- Logging system

### Deployment Strategies

**Blue-Green Deployment:**
- Zero-downtime deployments
- Easy rollback capability
- Traffic switching
- Health checks

**Canary Deployment:**
- Gradual rollout
- Real-time monitoring
- Automatic rollback on failure
- A/B testing support

## Prerequisites

### System Requirements

**Minimum Requirements (Development):**
- CPU: 4 cores
- RAM: 8GB
- Storage: 50GB SSD
- Network: 100Mbps
- OS: Ubuntu 20.04+, RHEL 8+, or equivalent

**Recommended Requirements (Production):**
- CPU: 16+ cores
- RAM: 32GB+
- Storage: 500GB+ SSD
- Network: 1Gbps+
- OS: Ubuntu 22.04 LTS, RHEL 9, or equivalent

### Software Requirements

**Container Runtime:**
- Docker 20.10+
- Docker Compose 2.0+

**Orchestration:**
- Kubernetes 1.25+
- kubectl 1.25+
- Helm 3.8+

**Development Tools:**
- Node.js 18+
- Python 3.11+
- Git 2.30+
- Make 4.0+

### Account Requirements

**Cloud Accounts:**
- AWS/GCP/Azure account with appropriate permissions
- Container registry access
- DNS management access
- Monitoring service access

**API Credentials:**
- AI model API keys (GLM-4.5, Claude 4.1 Opus)
- Database credentials
- SSL certificates
- Monitoring service credentials

## Environment Setup

### Development Environment

**Repository Setup:**
```bash
# Clone repository
git clone https://github.com/kyros/kyros-praxis.git
cd kyros-praxis

# Create development branch
git checkout -b develop

# Install dependencies
npm install
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration
```

**Docker Setup:**
```bash
# Verify Docker installation
docker --version
docker-compose --version

# Build development images
docker-compose build

# Start development environment
docker-compose up -d

# Verify services are running
docker-compose ps
curl http://localhost:3000/api/health
curl http://localhost:8000/healthz
```

### Local Development Tools

**IDE Configuration:**
```json
// .vscode/settings.json
{
    "python.linting.enabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.fixAll.eslint": true
    },
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.nosetestsEnabled": false
}
```

**Pre-commit Hooks:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-merge-conflict
      - id: debug-statements
      - id: check-added-large-files
      - id: check-case-conflict
      - id: check-docstring-first
  
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        additional_dependencies: [
            "flake8-docstrings",
            "flake8-bugbear",
            "flake8-comprehensions"
        ]
```

## Local Development Deployment

### Development Services Setup

**Docker Compose Development:**
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  console:
    build:
      context: ./services/console
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - NEXT_PUBLIC_ADK_URL=http://localhost:8000
    volumes:
      - ./services/console:/app
      - /app/node_modules
    depends_on:
      - orchestrator
    networks:
      - kyros-network

  orchestrator:
    build:
      context: ./services/orchestrator
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app
      - DATABASE_URL=postgresql://kyros:kyros@postgres:5432/kyros_dev
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./services/orchestrator:/app
      - ./packages:/app/packages
    depends_on:
      - postgres
      - redis
    networks:
      - kyros-network

  terminal-daemon:
    build:
      context: ./services/terminal-daemon
      dockerfile: Dockerfile.dev
    ports:
      - "8787:8787"
    environment:
      - NODE_ENV=development
    volumes:
      - ./services/terminal-daemon:/app
      - /app/node_modules
    networks:
      - kyros-network

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=kyros_dev
      - POSTGRES_USER=kyros
      - POSTGRES_PASSWORD=kyros
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - kyros-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - kyros-network

  pgadmin:
    image: dpage/pgadmin4:latest
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@kyros.com
      - PGADMIN_DEFAULT_PASSWORD=admin
    ports:
      - "8080:80"
    depends_on:
      - postgres
    networks:
      - kyros-network

volumes:
  postgres_data:
  redis_data:

networks:
  kyros-network:
    driver: bridge
```

**Development Scripts:**
```bash
#!/bin/bash
# scripts/dev-setup.sh

set -e

echo "🚀 Setting up Kyros development environment..."

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration before continuing"
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install
pip install -r requirements.txt

# Build development images
echo "🏗️  Building development images..."
docker-compose -f docker-compose.dev.yml build

# Start services
echo "🚀 Starting development services..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run health checks
echo "🔍 Running health checks..."
if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Console is healthy"
else
    echo "❌ Console is not responding"
fi

if curl -f http://localhost:8000/healthz > /dev/null 2>&1; then
    echo "✅ Orchestrator is healthy"
else
    echo "❌ Orchestrator is not responding"
fi

echo ""
echo "🎉 Development environment is ready!"
echo "📊 Console: http://localhost:3000"
echo "🔧 Orchestrator: http://localhost:8000"
echo "💻 Terminal Daemon: ws://localhost:8787"
echo "🗄️  pgAdmin: http://localhost:8080"
echo ""
echo "📚 Useful commands:"
echo "  docker-compose -f docker-compose.dev.yml logs -f [service]"
echo "  docker-compose -f docker-compose.dev.yml restart [service]"
echo "  docker-compose -f docker-compose.dev.yml down"
```

### Development Workflow

**Local Development Commands:**
```bash
# Start development environment
./scripts/dev-setup.sh

# View logs
docker-compose -f docker-compose.dev.yml logs -f console
docker-compose -f docker-compose.dev.yml logs -f orchestrator

# Restart services
docker-compose -f docker-compose.dev.yml restart console
docker-compose -f docker-compose.dev.yml restart orchestrator

# Stop services
docker-compose -f docker-compose.dev.yml down

# Clean build
docker-compose -f docker-compose.dev.yml down -v
docker system prune -f
```

**Database Setup:**
```bash
# Access PostgreSQL
docker-compose -f docker-compose.dev.yml exec postgres psql -U kyros -d kyros_dev

# Run migrations
docker-compose -f docker-compose.dev.yml exec orchestrator python -m alembic upgrade head

# Seed database
docker-compose -f docker-compose.dev.yml exec orchestrator python scripts/seed_database.py
```

## Production Deployment

### Production Architecture

**Production Infrastructure:**
```
                    ┌─────────────────┐
                    │   Load Balancer  │
                    │  (ALB/NLB/HAProxy) │
                    └─────────┬───────┘
                              │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼──────┐     ┌────────▼────────┐     ┌───────▼──────┐
│   Console     │     │  Orchestrator   │     │  Terminal    │
│   (Next.js)   │     │   (FastAPI)     │     │   Daemon     │
│   Pods: 3-6   │     │   Pods: 3-6    │     │   Pods: 2-3   │
└───────┬──────┘     └────────┬────────┘     └───────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                              │
                    ┌─────────▼───────┐
                    │   Database      │
                    │ (RDS/PostgreSQL)│
                    │   Multi-AZ      │
                    └─────────────────┘

                    ┌─────────────────┐
                    │   Monitoring    │
                    │ (Prometheus +   │
                    │   Grafana)       │
                    └─────────────────┘

                    ┌─────────────────┐
                    │   Logging       │
                    │ (ELK/CloudWatch)│
                    └─────────────────┘
```

### Kubernetes Deployment

**Helm Chart:**
```yaml
# charts/kyros/values.yaml
global:
  imagePullSecrets:
    - name: regcred
  
  # Database configuration
  database:
    host: "kyros-postgres.postgres.svc.cluster.local"
    port: 5432
    name: "kyros_prod"
    sslMode: "require"
  
  # Redis configuration
  redis:
    host: "kyros-redis.redis.svc.cluster.local"
    port: 6379
    password: ""

# Console configuration
console:
  enabled: true
  replicaCount: 3
  
  image:
    repository: kyros/console
    tag: "1.0.0"
    pullPolicy: IfNotPresent
  
  service:
    type: ClusterIP
    port: 3000
  
  ingress:
    enabled: true
    annotations:
      kubernetes.io/ingress.class: "nginx"
      cert-manager.io/cluster-issuer: "letsencrypt-prod"
    hosts:
      - host: kyros.yourdomain.com
        paths:
          - path: /
            pathType: Prefix
  
  resources:
    limits:
      cpu: "500m"
      memory: "512Mi"
    requests:
      cpu: "250m"
      memory: "256Mi"
  
  env:
    - name: NODE_ENV
      value: "production"
    - name: NEXT_PUBLIC_ADK_URL
      value: "https://api.kyros.yourdomain.com"
  
  livenessProbe:
    httpGet:
      path: /api/health
      port: 3000
    initialDelaySeconds: 30
    periodSeconds: 10
  
  readinessProbe:
    httpGet:
      path: /api/health
      port: 3000
    initialDelaySeconds: 5
    periodSeconds: 5

# Orchestrator configuration
orchestrator:
  enabled: true
  replicaCount: 3
  
  image:
    repository: kyros/orchestrator
    tag: "1.0.0"
    pullPolicy: IfNotPresent
  
  service:
    type: ClusterIP
    port: 8000
  
  ingress:
    enabled: true
    annotations:
      kubernetes.io/ingress.class: "nginx"
      cert-manager.io/cluster-issuer: "letsencrypt-prod"
    hosts:
      - host: api.kyros.yourdomain.com
        paths:
          - path: /
            pathType: Prefix
  
  resources:
    limits:
      cpu: "1000m"
      memory: "1Gi"
    requests:
      cpu: "500m"
      memory: "512Mi"
  
  env:
    - name: PYTHONPATH
      value: "/app"
    - name: DATABASE_URL
      valueFrom:
        secretKeyRef:
          name: kyros-secrets
          key: database-url
    - name: REDIS_URL
      valueFrom:
        secretKeyRef:
          name: kyros-secrets
          key: redis-url
  
  livenessProbe:
    httpGet:
      path: /healthz
      port: 8000
    initialDelaySeconds: 30
    periodSeconds: 10
  
  readinessProbe:
    httpGet:
      path: /healthz
      port: 8000
    initialDelaySeconds: 5
    periodSeconds: 5

# Terminal daemon configuration
terminalDaemon:
  enabled: true
  replicaCount: 2
  
  image:
    repository: kyros/terminal-daemon
    tag: "1.0.0"
    pullPolicy: IfNotPresent
  
  service:
    type: ClusterIP
    port: 8787
  
  resources:
    limits:
      cpu: "250m"
      memory: "256Mi"
    requests:
      cpu: "125m"
      memory: "128Mi"
  
  env:
    - name: NODE_ENV
      value: "production"

# Monitoring configuration
monitoring:
  enabled: true
  prometheus:
    enabled: true
    server:
      resources:
        limits:
          cpu: "500m"
          memory: "512Mi"
        requests:
          cpu: "250m"
          memory: "256Mi"
  
  grafana:
    enabled: true
    adminPassword: "admin"
    resources:
      limits:
        cpu: "250m"
        memory: "256Mi"
      requests:
        cpu: "125m"
        memory: "128Mi"

# Security configuration
security:
  enabled: true
  podSecurityContext:
    fsGroup: 1000
    runAsUser: 1000
    runAsNonRoot: true
  
  networkPolicy:
    enabled: true
  
  rbac:
    enabled: true
```

**Kubernetes Deployment Manifests:**
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: kyros
  labels:
    name: kyros
    app: kyros

---
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: kyros-secrets
  namespace: kyros
type: Opaque
stringData:
  database-url: "postgresql://kyros:${KYROS_DB_PASSWORD}@kyros-postgres:5432/kyros_prod"
  redis-url: "redis://:${KYROS_REDIS_PASSWORD}@kyros-redis:6379"
  jwt-secret: "${KYROS_JWT_SECRET}"
  glm-api-key: "${GLM_API_KEY}"
  claude-api-key: "${CLAUDE_API_KEY}"
  webhook-secret: "${WEBHOOK_SECRET}"

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kyros-config
  namespace: kyros
data:
  # Application configuration
  APP_ENV: "production"
  LOG_LEVEL: "INFO"
  
  # Model configuration
  DEFAULT_MODEL: "glm-4.5"
  ESCALATION_MODEL: "claude-4.1-opus"
  MODEL_TIMEOUT: "300"
  
  # Rate limiting
  RATE_LIMIT_REQUESTS: "1000"
  RATE_LIMIT_WINDOW: "3600"
  
  # Database configuration
  DB_POOL_SIZE: "20"
  DB_MAX_OVERFLOW: "10"
  DB_POOL_RECYCLE: "3600"
  
  # Redis configuration
  REDIS_POOL_SIZE: "10"
  REDIS_TIMEOUT: "5"
  
  # Monitoring configuration
  METRICS_PORT: "8080"
  HEALTH_CHECK_INTERVAL: "30"
  
  # Security configuration
  JWT_EXPIRATION_HOURS: "24"
  MAX_LOGIN_ATTEMPTS: "5"
  SESSION_TIMEOUT_MINUTES: "30"
```

### Deployment Scripts

**Production Deployment Script:**
```bash
#!/bin/bash
# scripts/deploy-production.sh

set -euo pipefail

# Configuration
KUBECONFIG="${KUBECONFIG:-$HOME/.kube/config}"
NAMESPACE="kyros"
CHART_PATH="./charts/kyros"
RELEASE_NAME="kyros-prod"
VALUES_FILE="./charts/kyros/values-production.yaml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Pre-deployment checks
log_info "Running pre-deployment checks..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Check if helm is available
if ! command -v helm &> /dev/null; then
    log_error "helm is not installed or not in PATH"
    exit 1
fi

# Check if we can connect to the cluster
if ! kubectl cluster-info &> /dev/null; then
    log_error "Cannot connect to Kubernetes cluster"
    exit 1
fi

# Create namespace if it doesn't exist
log_info "Creating namespace..."
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Create secrets
log_info "Creating secrets..."
kubectl create secret generic kyros-secrets \
    --namespace="$NAMESPACE" \
    --from-literal=database-url="$DATABASE_URL" \
    --from-literal=redis-url="$REDIS_URL" \
    --from-literal=jwt-secret="$JWT_SECRET" \
    --from-literal=glm-api-key="$GLM_API_KEY" \
    --from-literal=claude-api-key="$CLAUDE_API_KEY" \
    --from-literal=webhook-secret="$WEBHOOK_SECRET" \
    --dry-run=client -o yaml | kubectl apply -f -

# Create configmap
log_info "Creating configmap..."
kubectl create configmap kyros-config \
    --namespace="$NAMESPACE" \
    --from-file=config/production.env \
    --dry-run=client -o yaml | kubectl apply -f -

# Update Helm dependencies
log_info "Updating Helm dependencies..."
helm dependency update "$CHART_PATH"

# Upgrade or install the release
log_info "Deploying Kyros..."
if helm status -n "$NAMESPACE" "$RELEASE_NAME" &> /dev/null; then
    log_info "Upgrading existing release..."
    helm upgrade "$RELEASE_NAME" \
        "$CHART_PATH" \
        --namespace="$NAMESPACE" \
        --values="$VALUES_FILE" \
        --wait \
        --timeout=600s
else
    log_info "Installing new release..."
    helm install "$RELEASE_NAME" \
        "$CHART_PATH" \
        --namespace="$NAMESPACE" \
        --values="$VALUES_FILE" \
        --wait \
        --timeout=600s
fi

# Post-deployment checks
log_info "Running post-deployment checks..."

# Wait for deployments to be ready
kubectl wait --for=condition=ready pod \
    --namespace="$NAMESPACE" \
    --selector=app=kyros \
    --timeout=300s

# Run health checks
log_info "Running health checks..."
kubectl get pods -n "$NAMESPACE" -l app=kyros

# Check service endpoints
log_info "Checking service endpoints..."
kubectl get endpoints -n "$NAMESPACE"

# Verify deployment
log_info "Verifying deployment..."
DEPLOYMENTS=("console" "orchestrator" "terminal-daemon")
for deployment in "${DEPLOYMENTS[@]}"; do
    if kubectl get deployment -n "$NAMESPACE" "$deployment" &> /dev/null; then
        REPLICAS=$(kubectl get deployment -n "$NAMESPACE" "$deployment" -o jsonpath='{.spec.replicas}')
        READY_REPLICAS=$(kubectl get deployment -n "$NAMESPACE" "$deployment" -o jsonpath='{.status.readyReplicas}')
        
        if [[ "$READY_REPLICAS" -eq "$REPLICAS" ]]; then
            log_info "✅ $deployment deployment successful ($READY_REPLICAS/$REPLICAS replicas ready)"
        else
            log_warn "⚠️  $deployment deployment partially ready ($READY_REPLICAS/$REPLICAS replicas ready)"
        fi
    else
        log_error "❌ $deployment deployment not found"
    fi
done

# Display access information
log_info "🎉 Deployment completed successfully!"
log_info "📊 Access URLs:"
kubectl get ingress -n "$NAMESPACE" -o jsonpath='{range .items[*]}http://{.spec.rules[0].host}{.spec.rules[0].http.paths[0].path}{"\n"}{end}'

log_info "📝 Useful commands:"
log_info "  kubectl get pods -n $NAMESPACE"
log_info "  kubectl logs -n $NAMESPACE -l app=kyros"
log_info "  kubectl get events -n $NAMESPACE"
log_info "  helm status -n $NAMESPACE $RELEASE_NAME"
log_info "  helm history -n $NAMESPACE $RELEASE_NAME"
```

## Cloud Deployment

### AWS Deployment

**AWS Infrastructure as Code:**
```yaml
# terraform/aws/main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# EKS Cluster
resource "aws_eks_cluster" "kyros" {
  name     = var.cluster_name
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "1.25"

  vpc_config {
    subnet_ids = aws_subnet.kyros[*].id
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_AmazonEKSClusterPolicy,
  ]
}

# Node Group
resource "aws_eks_node_group" "kyros" {
  cluster_name    = aws_eks_cluster.kyros.name
  node_group_name = "kyros-node-group"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = aws_subnet.kyros[*].id

  scaling_config {
    desired_size = 3
    max_size     = 10
    min_size     = 1
  }

  instance_types = ["t3.medium", "t3.large"]

  depends_on = [
    aws_iam_role_policy_attachment.eks_node_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.eks_node_AmazonEKS_CNI_Policy,
  ]
}

# RDS PostgreSQL
resource "aws_db_instance" "kyros" {
  identifier           = "kyros-postgres"
  engine               = "postgres"
  engine_version       = "15"
  instance_class       = "db.t3.medium"
  allocated_storage    = 100
  storage_type         = "gp2"
  storage_encrypted   = true
  multi_az            = true
  username            = "kyros"
  password            = var.db_password
  db_name             = "kyros_prod"
  parameter_group_name = "default.postgres15"
  skip_final_snapshot = false

  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = aws_db_subnet_group.kyros.name

  lifecycle {
    prevent_destroy = false
  }
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "kyros" {
  cluster_id           = "kyros-redis"
  engine               = "redis"
  engine_version       = "7.0"
  node_type            = "cache.t3.medium"
  port                 = 6379
  num_cache_nodes      = 2
  parameter_group_name = aws_elasticache_parameter_group.kyros.name
  security_group_ids  = [aws_security_group.redis.id]
  subnet_group_name    = aws_elasticache_subnet_group.kyros
}

# Application Load Balancer
resource "aws_lb" "kyros" {
  name               = "kyros-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = aws_subnet.kyros[*].id

  enable_deletion_protection = true

  access_logs {
    bucket  = aws_s3_bucket.alb_logs.id
    prefix  = "alb"
    enabled = true
  }
}

# Route53
resource "aws_route53_record" "kyros" {
  zone_id = data.aws_route53_zone.kyros.id
  name    = "kyros.${data.aws_route53_zone.kyros.name}"
  type    = "A"

  alias {
    name                   = aws_lb.kyros.dns_name
    zone_id                = aws_lb.kyros.zone_id
    evaluate_target_health = true
  }
}

# S3 for logs
resource "aws_s3_bucket" "alb_logs" {
  bucket = "kyros-alb-logs-${var.aws_region}"

  lifecycle {
    prevent_destroy = false
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "kyros" {
  name              = "/aws/eks/kyros/cluster"
  retention_in_days = 30
}

# IAM Roles
resource "aws_iam_role" "eks_cluster" {
  name = "kyros-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role" "eks_node" {
  name = "kyros-eks-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

# Security Groups
resource "aws_security_group" "alb" {
  name        = "kyros-alb-sg"
  description = "Security group for ALB"
  vpc_id      = aws_vpc.kyros.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "eks" {
  name        = "kyros-eks-sg"
  description = "Security group for EKS"
  vpc_id      = aws_vpc.kyros.id

  ingress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Outputs
output "cluster_endpoint" {
  value = aws_eks_cluster.kyros.endpoint
}

output "cluster_name" {
  value = aws_eks_cluster.kyros.name
}

output "alb_dns_name" {
  value = aws_lb.kyros.dns_name
}

output "db_endpoint" {
  value = aws_db_instance.kyros.endpoint
}

output "redis_endpoint" {
  value = aws_elasticache_cluster.kyros.cache_nodes[0].address
}
```

### GCP Deployment

**GCP Kubernetes Deployment:**
```yaml
# gcp/cloudbuild.yaml
steps:
  # Build and push Docker images
  - name: 'gcr.io/cloud-builders/docker'
    id: 'build-console'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/console:$COMMIT_SHA', './services/console']
  
  - name: 'gcr.io/cloud-builders/docker'
    id: 'push-console'
    args: ['push', 'gcr.io/$PROJECT_ID/console:$COMMIT_SHA']
  
  - name: 'gcr.io/cloud-builders/docker'
    id: 'build-orchestrator'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/orchestrator:$COMMIT_SHA', './services/orchestrator']
  
  - name: 'gcr.io/cloud-builders/docker'
    id: 'push-orchestrator'
    args: ['push', 'gcr.io/$PROJECT_ID/orchestrator:$COMMIT_SHA']
  
  - name: 'gcr.io/cloud-builders/docker'
    id: 'build-terminal-daemon'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/terminal-daemon:$COMMIT_SHA', './services/terminal-daemon']
  
  - name: 'gcr.io/cloud-builders/docker'
    id: 'push-terminal-daemon'
    args: ['push', 'gcr.io/$PROJECT_ID/terminal-daemon:$COMMIT_SHA']
  
  # Deploy to GKE
  - name: 'gcr.io/cloud-builders/kubectl'
    id: 'deploy-gke'
    env:
      - 'CLOUDSDK_CONTAINER_CLUSTER=kyros-cluster'
      - 'CLOUDSDK_COMPUTE_ZONE=us-central1-a'
    args:
      - 'apply'
      - '-f'
      - 'k8s/'
      - '--image=console=gcr.io/$PROJECT_ID/console:$COMMIT_SHA'
      - '--image=orchestrator=gcr.io/$PROJECT_ID/orchestrator:$COMMIT_SHA'
      - '--image=terminal-daemon=gcr.io/$PROJECT_ID/terminal-daemon:$COMMIT_SHA'
  
  # Wait for deployment
  - name: 'gcr.io/cloud-builders/kubectl'
    id: 'wait-deployment'
    env:
      - 'CLOUDSDK_CONTAINER_CLUSTER=kyros-cluster'
      - 'CLOUDSDK_COMPUTE_ZONE=us-central1-a'
    args:
      - 'wait'
      - '--for=condition=ready'
      - 'pod'
      - '-l'
      'app=kyros'
      - '--timeout=600s'
  
  # Run tests
  - name: 'gcr.io/cloud-builders/kubectl'
    id: 'run-tests'
    env:
      - 'CLOUDSDK_CONTAINER_CLUSTER=kyros-cluster'
      - 'CLOUDSDK_COMPUTE_ZONE=us-central1-a'
    args:
      - 'exec'
      - 'deployment/console-xxxxx'
      - '--'
      'npm'
      'test'
  
  # Get deployment status
  - name: 'gcr.io/cloud-builders/kubectl'
    id: 'get-status'
    env:
      - 'CLOUDSDK_CONTAINER_CLUSTER=kyros-cluster'
      - 'CLOUDSDK_COMPUTE_ZONE=us-central1-a'
    args:
      - 'get'
      'pods'
      - '-l'
      'app=kyros'

images:
  - 'gcr.io/$PROJECT_ID/console:$COMMIT_SHA'
  - 'gcr.io/$PROJECT_ID/orchestrator:$COMMIT_SHA'
  - 'gcr.io/$PROJECT_ID/terminal-daemon:$COMMIT_SHA'
```

## High Availability Deployment

### Multi-Region Deployment

**Global Architecture:**
```
Region 1 (us-east-1)              Region 2 (us-west-2)
┌─────────────────┐              ┌─────────────────┐
│   Load Balancer│              │   Load Balancer│
│   (Cloudflare)  │              │   (Cloudflare)  │
└────────┬────────┘              └────────┬────────┘
         │                               │
         ▼                               ▼
┌─────────────────┐              ┌─────────────────┐
│   Kubernetes    │              │   Kubernetes    │
│   Cluster       │              │   Cluster       │
│                 │              │                 │
│ Console Pods   │              │ Console Pods   │
│ Orchestrator   │              │ Orchestrator   │
│ Terminal Daemon│              │ Terminal Daemon│
│                 │              │                 │
└────────┬────────┘              └────────┬────────┘
         │                               │
         ▼                               ▼
┌─────────────────┐              ┌─────────────────┐
│   Regional DB   │              │   Regional DB   │
│   (RDS Multi-AZ)│              │   (RDS Multi-AZ)│
│                 │              │                 │
│ Primary Region │              │ Secondary Region│
└─────────────────┘              └─────────────────┘
         │                               │
         └───────────────┬─────────────────────┘
                         ▼
                ┌─────────────────┐
                │   Global DNS     │
                │   (Route53)      │
                └─────────────────┘
```

**Multi-Region Deployment Script:**
```bash
#!/bin/bash
# scripts/deploy-multiregion.sh

set -euo pipefail

# Configuration
REGIONS=("us-east-1" "us-west-2")
PROJECT_ID="kyros-prod"
CLUSTER_NAME="kyros-cluster"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
log_info "Checking prerequisites..."

if ! command -v gcloud &> /dev/null; then
    log_error "gcloud CLI is not installed"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    log_error "kubectl is not installed"
    exit 1
fi

# Authenticate with GCP
log_info "Authenticating with GCP..."
gcloud auth login
gcloud config set project "$PROJECT_ID"

# Deploy to each region
for region in "${REGIONS[@]}"; do
    log_info "Deploying to region: $region"
    
    # Set gcloud region
    gcloud config set compute/region "$region"
    
    # Create GKE cluster
    log_info "Creating GKE cluster in $region..."
    gcloud container clusters create "$CLUSTER_NAME" \
        --region="$region" \
        --node-locations="$region-a,$region-b,$region-c" \
        --num-nodes=3 \
        --machine-type="e2-medium" \
        --image-type="COS_CONTAINERD" \
        --disk-type="pd-standard" \
        --disk-size="100" \
        --enable-autoscaling \
        --min-nodes=1 \
        --max-nodes=10 \
        --enable-autorepair \
        --enable-upgrade \
        --enable-stackdriver-kubernetes \
        --enable-ip-alias \
        --enable-private-nodes \
        --master-ipv4-cidr="172.16.0.0/28"
    
    # Get cluster credentials
    log_info "Getting cluster credentials..."
    gcloud container clusters get-credentials "$CLUSTER_NAME" --region="$region"
    
    # Create namespace
    kubectl create namespace kyros --dry-run=client -o yaml | kubectl apply -f -
    
    # Create secrets
    log_info "Creating secrets in $region..."
    kubectl create secret generic kyros-secrets \
        --namespace=kyros \
        --from-literal=database-url="$DATABASE_URL" \
        --from-literal=redis-url="$REDIS_URL" \
        --from-literal=jwt-secret="$JWT_SECRET" \
        --from-literal=glm-api-key="$GLM_API_KEY" \
        --from-literal=claude-api-key="$CLAUDE_API_KEY" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy applications
    log_info "Deploying applications in $region..."
    kubectl apply -f k8s/ --namespace=kyros
    
    # Wait for deployment
    log_info "Waiting for deployment in $region..."
    kubectl wait --for=condition=ready pod \
        --namespace=kyros \
        --selector=app=kyros \
        --timeout=600s
    
    # Verify deployment
    log_info "Verifying deployment in $region..."
    kubectl get pods -n kyros -l app=kyros
    
    # Set up regional database
    log_info "Setting up regional database in $region..."
    gcloud sql instances create "kyros-db-$region" \
        --database-version=POSTGRES_15 \
        --region="$region" \
        --tier=db-custom-2-3840 \
        --storage-type=PD_SSD \
        --storage-size=100 \
        --availability-type=ZONAL \
        --backup-config="BACKUP_BY_DAY"
    
    # Set up regional Redis
    log_info "Setting up regional Redis in $region..."
    gcloud redis instances create "kyros-redis-$region" \
        --region="$region" \
        --tier="STANDARD_HA" \
        --memory-size-gb=2 \
        --redis-version="7.0"
    
    # Update regional configuration
    log_info "Updating regional configuration..."
    cat > "k8s/values-$region.yaml" << EOF
global:
  region: $region
  project: $PROJECT_ID

database:
  host: "10.1.2.3"  # Replace with actual DB IP
  name: "kyros_prod"
  
redis:
  host: "10.1.2.4"  # Replace with actual Redis IP
  
monitoring:
  region: $region
  project: $PROJECT_ID
EOF
    
    log_info "✅ Deployment to $region completed successfully"
done

# Set up global DNS
log_info "Setting up global DNS..."
cat > "dns/global.yaml" << EOF
apiVersion: networking.gke.io/v1
kind: MultiClusterIngress
metadata:
  name: kyros-global
  namespace: kyros
spec:
  template:
    spec:
      rules:
      - host: kyros.yourdomain.com
        http:
          paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: kyros-console
                port:
                  number: 3000
EOF

# Apply global DNS configuration
kubectl apply -f dns/global.yaml

# Set up health checks between regions
log_info "Setting up inter-region health checks..."
for region in "${REGIONS[@]}"; do
    for other_region in "${REGIONS[@]}"; do
        if [[ "$region" != "$other_region" ]]; then
            log_info "Setting up health check from $region to $other_region"
            
            # Create health check service
            cat > "k8s/health-check-$region-to-$other_region.yaml" << EOF
apiVersion: v1
kind: Service
metadata:
  name: health-check-$other_region
  namespace: kyros
  annotations:
    external-dns.alpha.kubernetes.io/hostname: "health-$other_region.kyros.yourdomain.com"
spec:
  type: ExternalName
  externalName: "kyros-console.$other_region.kyros.yourdomain.com"
EOF
            
            kubectl apply -f "k8s/health-check-$region-to-$other_region.yaml"
        fi
    done
done

log_info "🎉 Multi-region deployment completed successfully!"
log_info "📊 Access URLs:"
for region in "${REGIONS[@]}"; do
    echo "  Region $region: https://kyros.yourdomain.com (traffic routed automatically)"
done

log_info "📝 Health check URLs:"
for region in "${REGIONS[@]}"; do
    for other_region in "${REGIONS[@]}"; do
        if [[ "$region" != "$other_region" ]]; then
            echo "  $region to $other_region: https://health-$other_region.kyros.yourdomain.com"
        fi
    done
done
```

## Configuration Management

### Environment Configuration

**Development Configuration:**
```yaml
# config/development.yaml
app:
  name: "Kyros"
  environment: "development"
  debug: true
  log_level: "DEBUG"

server:
  host: "0.0.0.0"
  port: 8000
  workers: 1
  reload: true

database:
  url: "postgresql://kyros:kyros@localhost:5432/kyros_dev"
  pool_size: 5
  max_overflow: 10
  pool_recycle: 3600
  echo: true

redis:
  url: "redis://localhost:6379"
  pool_size: 5
  timeout: 5
  decode_responses: true

models:
  default: "glm-4.5"
  escalation: "claude-4.1-opus"
  timeout: 300
  temperature: 0.7
  max_tokens: 2000

security:
  secret_key: "dev-secret-key"
  jwt_algorithm: "HS256"
  jwt_expiration: 86400
  session_timeout: 1800
  max_login_attempts: 5

monitoring:
  metrics_enabled: true
  metrics_port: 8080
  health_check_interval: 30
  logging_level: "DEBUG"

cors:
  allow_origins: ["http://localhost:3000", "http://127.0.0.1:3000"]
  allow_credentials: true
  allow_methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
  allow_headers: ["*"]

rate_limiting:
  enabled: true
  requests_per_minute: 1000
  burst_limit: 100
```

**Production Configuration:**
```yaml
# config/production.yaml
app:
  name: "Kyros"
  environment: "production"
  debug: false
  log_level: "INFO"

server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  reload: false

database:
  url: "${DATABASE_URL}"
  pool_size: 20
  max_overflow: 10
  pool_recycle: 3600
  echo: false
  ssl_mode: "require"

redis:
  url: "${REDIS_URL}"
  pool_size: 10
  timeout: 5
  decode_responses: true
  ssl: true

models:
  default: "glm-4.5"
  escalation: "claude-4.1-opus"
  timeout: 300
  temperature: 0.7
  max_tokens: 2000
  fallback_model: "glm-4.5"

security:
  secret_key: "${JWT_SECRET}"
  jwt_algorithm: "HS256"
  jwt_expiration: 86400
  session_timeout: 1800
  max_login_attempts: 5
  password_min_length: 8
  password_require_special: true

monitoring:
  metrics_enabled: true
  metrics_port: 8080
  health_check_interval: 30
  logging_level: "INFO"
  log_rotation: true
  log_retention_days: 30

cors:
  allow_origins: ["https://kyros.yourdomain.com"]
  allow_credentials: true
  allow_methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
  allow_headers: ["*"]

rate_limiting:
  enabled: true
  requests_per_minute: 1000
  burst_limit: 100
  block_time: 300

backup:
  enabled: true
  schedule: "0 2 * * *"
  retention_days: 30
  compression: true
  encryption: true

scaling:
  min_replicas: 3
  max_replicas: 10
  target_cpu_utilization: 70
  target_memory_utilization: 80
  scale_up_cooldown: 300
  scale_down_cooldown: 300
```

### Configuration Loading

**Python Configuration Loader:**
```python
import os
import yaml
from typing import Dict, Any
from pathlib import Path

class ConfigLoader:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from YAML files and environment variables"""
        # Load base configuration
        base_config = self._load_yaml_file("base.yaml")
        self.config.update(base_config)
        
        # Load environment-specific configuration
        env = os.getenv("APP_ENV", "development")
        env_config = self._load_yaml_file(f"{env}.yaml")
        self._merge_config(env_config)
        
        # Load local configuration (for development overrides)
        local_config = self._load_yaml_file("local.yaml", optional=True)
        if local_config:
            self._merge_config(local_config)
        
        # Override with environment variables
        self._apply_env_overrides()
    
    def _load_yaml_file(self, filename: str, optional: bool = False) -> Dict[str, Any]:
        """Load YAML configuration file"""
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            if optional:
                return {}
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _merge_config(self, new_config: Dict[str, Any]):
        """Merge new configuration with existing config"""
        def deep_merge(base: Dict, update: Dict) -> Dict:
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    base[key] = deep_merge(base[key], value)
                else:
                    base[key] = value
            return base
        
        self.config = deep_merge(self.config, new_config)
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides"""
        env_mapping = {
            "DATABASE_URL": ["database", "url"],
            "REDIS_URL": ["redis", "url"],
            "JWT_SECRET": ["security", "secret_key"],
            "GLM_API_KEY": ["models", "glm_api_key"],
            "CLAUDE_API_KEY": ["models", "claude_api_key"],
            "LOG_LEVEL": ["app", "log_level"],
            "SERVER_PORT": ["server", "port"],
            "WORKERS": ["server", "workers"],
            "METRICS_PORT": ["monitoring", "metrics_port"],
            "ENABLE_METRICS": ["monitoring", "metrics_enabled"],
            "REDIS_POOL_SIZE": ["redis", "pool_size"],
            "DB_POOL_SIZE": ["database", "pool_size"],
            "RATE_LIMIT_REQUESTS": ["rate_limiting", "requests_per_minute"],
            "CORS_ORIGINS": ["cors", "allow_origins"],
            "BACKUP_ENABLED": ["backup", "enabled"],
            "MIN_REPLICAS": ["scaling", "min_replicas"],
            "MAX_REPLICAS": ["scaling", "max_replicas"],
        }
        
        for env_var, config_path in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert string values to appropriate types
                converted_value = self._convert_env_value(env_value)
                
                # Set value in config
                current = self.config
                for key in config_path[:-1]:
                    current = current.setdefault(key, {})
                current[config_path[-1]] = converted_value
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type"""
        # Boolean values
        if value.lower() in ['true', 'false', '1', '0']:
            return value.lower() in ['true', '1']
        
        # Integer values
        if value.isdigit():
            return int(value)
        
        # Float values
        try:
            return float(value)
        except ValueError:
            pass
        
        # Comma-separated lists
        if ',' in value:
            return [item.strip() for item in value.split(',')]
        
        # JSON values
        if value.startswith('{') and value.endswith('}'):
            try:
                import json
                return json.loads(value)
            except:
                pass
        
        # Return as string
        return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        current = self.config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def get_database_url(self) -> str:
        """Get database URL with fallbacks"""
        return os.getenv("DATABASE_URL", self.get("database.url"))
    
    def get_redis_url(self) -> str:
        """Get Redis URL with fallbacks"""
        return os.getenv("REDIS_URL", self.get("redis.url"))
    
    def get_jwt_secret(self) -> str:
        """Get JWT secret with fallbacks"""
        return os.getenv("JWT_SECRET", self.get("security.secret_key"))
    
    def get_model_api_keys(self) -> Dict[str, str]:
        """Get model API keys"""
        return {
            "glm": os.getenv("GLM_API_KEY", self.get("models.glm_api_key")),
            "claude": os.getenv("CLAUDE_API_KEY", self.get("models.claude_api_key")),
        }
    
    def validate_config(self) -> bool:
        """Validate configuration"""
        required_fields = [
            "app.name",
            "app.environment",
            "database.url",
            "redis.url",
            "security.secret_key",
            "models.default",
            "models.escalation",
        ]
        
        for field in required_fields:
            if self.get(field) is None:
                print(f"❌ Missing required configuration: {field}")
                return False
        
        # Validate URLs
        if not self.get_database_url():
            print("❌ Database URL is required")
            return False
        
        if not self.get_redis_url():
            print("❌ Redis URL is required")
            return False
        
        # Validate secrets
        if not self.get_jwt_secret():
            print("❌ JWT secret is required")
            return False
        
        # Validate model API keys in production
        if self.get("app.environment") == "production":
            api_keys = self.get_model_api_keys()
            for model, key in api_keys.items():
                if not key:
                    print(f"❌ {model.upper()} API key is required in production")
                    return False
        
        print("✅ Configuration validation passed")
        return True
    
    def __str__(self) -> str:
        """String representation of configuration"""
        return yaml.dump(self.config, default_flow_style=False)

# Usage
if __name__ == "__main__":
    config = ConfigLoader()
    
    print("📋 Current Configuration:")
    print(config)
    
    print("\n🔍 Validation:")
    if config.validate_config():
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration is invalid")
    
    print("\n🔑 Database URL:", config.get_database_url())
    print("🔑 Redis URL:", config.get_redis_url())
    print("🔑 JWT Secret:", config.get_jwt_secret()[:10] + "...")
    print("🤖 Model API Keys:", list(config.get_model_api_keys().keys()))
```

### Configuration Validation

**Configuration Validation Script:**
```python
#!/usr/bin/env python3
# scripts/validate_config.py

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any

class ConfigValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_all(self) -> bool:
        """Validate all configuration files"""
        print("🔍 Validating configuration files...")
        
        # Check configuration files exist
        self._check_config_files()
        
        # Validate YAML syntax
        self._validate_yaml_syntax()
        
        # Validate configuration values
        self._validate_configuration_values()
        
        # Validate environment variables
        self._validate_environment_variables()
        
        # Check for sensitive data
        self._check_sensitive_data()
        
        # Report results
        self._report_results()
        
        return len(self.errors) == 0
    
    def _check_config_files(self):
        """Check that required configuration files exist"""
        print("📁 Checking configuration files...")
        
        required_files = [
            "config/base.yaml",
            "config/development.yaml",
            "config/production.yaml"
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                self.errors.append(f"Required configuration file missing: {file_path}")
            else:
                print(f"✅ Found: {file_path}")
    
    def _validate_yaml_syntax(self):
        """Validate YAML syntax in configuration files"""
        print("📝 Validating YAML syntax...")
        
        config_files = [
            "config/base.yaml",
            "config/development.yaml",
            "config/production.yaml",
            "config/local.yaml"
        ]
        
        for file_path in config_files:
            if Path(file_path).exists():
                try:
                    with open(file_path, 'r') as f:
                        yaml.safe_load(f)
                    print(f"✅ Valid YAML: {file_path}")
                except yaml.YAMLError as e:
                    self.errors.append(f"Invalid YAML in {file_path}: {e}")
    
    def _validate_configuration_values(self):
        """Validate configuration values"""
        print("🔧 Validating configuration values...")
        
        config_files = [
            "config/development.yaml",
            "config/production.yaml"
        ]
        
        for file_path in config_files:
            if Path(file_path).exists():
                print(f"\n📋 Validating {file_path}...")
                self._validate_config_file(file_path)
    
    def _validate_config_file(self, file_path: str):
        """Validate a specific configuration file"""
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate app configuration
        if 'app' in config:
            self._validate_app_config(config['app'])
        
        # Validate server configuration
        if 'server' in config:
            self._validate_server_config(config['server'])
        
        # Validate database configuration
        if 'database' in config:
            self._validate_database_config(config['database'])
        
        # Validate redis configuration
        if 'redis' in config:
            self._validate_redis_config(config['redis'])
        
        # Validate models configuration
        if 'models' in config:
            self._validate_models_config(config['models'])
        
        # Validate security configuration
        if 'security' in config:
            self._validate_security_config(config['security'])
        
        # Validate monitoring configuration
        if 'monitoring' in config:
            self._validate_monitoring_config(config['monitoring'])
        
        # Validate CORS configuration
        if 'cors' in config:
            self._validate_cors_config(config['cors'])
        
        # Validate rate limiting configuration
        if 'rate_limiting' in config:
            self._validate_rate_limiting_config(config['rate_limiting'])
    
    def _validate_app_config(self, app_config: Dict[str, Any]):
        """Validate app configuration"""
        required_fields = ['name', 'environment']
        
        for field in required_fields:
            if field not in app_config:
                self.errors.append(f"Missing required field in app config: {field}")
        
        # Validate environment
        if 'environment' in app_config:
            valid_environments = ['development', 'testing', 'staging', 'production']
            if app_config['environment'] not in valid_environments:
                self.errors.append(f"Invalid environment: {app_config['environment']}")
        
        print(f"✅ App configuration validated")
    
    def _validate_server_config(self, server_config: Dict[str, Any]):
        """Validate server configuration"""
        required_fields = ['host', 'port']
        
        for field in required_fields:
            if field not in server_config:
                self.errors.append(f"Missing required field in server config: {field}")
        
        # Validate port
        if 'port' in server_config:
            port = server_config['port']
            if not isinstance(port, int) or port < 1 or port > 65535:
                self.errors.append(f"Invalid port number: {port}")
        
        # Validate workers
        if 'workers' in server_config:
            workers = server_config['workers']
            if not isinstance(workers, int) or workers < 1:
                self.errors.append(f"Invalid number of workers: {workers}")
        
        print(f"✅ Server configuration validated")
    
    def _validate_database_config(self, db_config: Dict[str, Any]):
        """Validate database configuration"""
        required_fields = ['url', 'pool_size']
        
        for field in required_fields:
            if field not in db_config:
                self.errors.append(f"Missing required field in database config: {field}")
        
        # Validate pool size
        if 'pool_size' in db_config:
            pool_size = db_config['pool_size']
            if not isinstance(pool_size, int) or pool_size < 1:
                self.errors.append(f"Invalid database pool size: {pool_size}")
        
        # Validate max overflow
        if 'max_overflow' in db_config:
            max_overflow = db_config['max_overflow']
            if not isinstance(max_overflow, int) or max_overflow < 0:
                self.errors.append(f"Invalid database max overflow: {max_overflow}")
        
        print(f"✅ Database configuration validated")
    
    def _validate_redis_config(self, redis_config: Dict[str, Any]):
        """Validate Redis configuration"""
        required_fields = ['url', 'pool_size']
        
        for field in required_fields:
            if field not in redis_config:
                self.errors.append(f"Missing required field in Redis config: {field}")
        
        # Validate pool size
        if 'pool_size' in redis_config:
            pool_size = redis_config['pool_size']
            if not isinstance(pool_size, int) or pool_size < 1:
                self.errors.append(f"Invalid Redis pool size: {pool_size}")
        
        # Validate timeout
        if 'timeout' in redis_config:
            timeout = redis_config['timeout']
            if not isinstance(timeout, (int, float)) or timeout < 0:
                self.errors.append(f"Invalid Redis timeout: {timeout}")
        
        print(f"✅ Redis configuration validated")
    
    def _validate_models_config(self, models_config: Dict[str, Any]):
        """Validate models configuration"""
        required_fields = ['default', 'escalation']
        
        for field in required_fields:
            if field not in models_config:
                self.errors.append(f"Missing required field in models config: {field}")
        
        # Validate timeout
        if 'timeout' in models_config:
            timeout = models_config['timeout']
            if not isinstance(timeout, (int, float)) or timeout < 0:
                self.errors.append(f"Invalid models timeout: {timeout}")
        
        # Validate temperature
        if 'temperature' in models_config:
            temperature = models_config['temperature']
            if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 1:
                self.errors.append(f"Invalid models temperature: {temperature}")
        
        print(f"✅ Models configuration validated")
    
    def _validate_security_config(self, security_config: Dict[str, Any]):
        """Validate security configuration"""
        required_fields = ['secret_key', 'jwt_algorithm']
        
        for field in required_fields:
            if field not in security_config:
                self.errors.append(f"Missing required field in security config: {field}")
        
        # Validate JWT algorithm
        if 'jwt_algorithm' in security_config:
            algorithm = security_config['jwt_algorithm']
            valid_algorithms = ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']
            if algorithm not in valid_algorithms:
                self.errors.append(f"Invalid JWT algorithm: {algorithm}")
        
        # Validate JWT expiration
        if 'jwt_expiration' in security_config:
            expiration = security_config['jwt_expiration']
            if not isinstance(expiration, (int, float)) or expiration < 0:
                self.errors.append(f"Invalid JWT expiration: {expiration}")
        
        # Validate session timeout
        if 'session_timeout' in security_config:
            timeout = security_config['session_timeout']
            if not isinstance(timeout, (int, float)) or timeout < 0:
                self.errors.append(f"Invalid session timeout: {timeout}")
        
        print(f"✅ Security configuration validated")
    
    def _validate_monitoring_config(self, monitoring_config: Dict[str, Any]):
        """Validate monitoring configuration"""
        # Validate metrics port
        if 'metrics_port' in monitoring_config:
            port = monitoring_config['metrics_port']
            if not isinstance(port, int) or port < 1 or port > 65535:
                self.errors.append(f"Invalid metrics port: {port}")
        
        # Validate health check interval
        if 'health_check_interval' in monitoring_config:
            interval = monitoring_config['health_check_interval']
            if not isinstance(interval, (int, float)) or interval < 0:
                self.errors.append(f"Invalid health check interval: {interval}")
        
        print(f"✅ Monitoring configuration validated")
    
    def _validate_cors_config(self, cors_config: Dict[str, Any]):
        """Validate CORS configuration"""
        if 'allow_origins' in cors_config:
            origins = cors_config['allow_origins']
            if not isinstance(origins, list):
                self.errors.append(f"Invalid CORS allow_origins: must be a list")
        
        if 'allow_methods' in cors_config:
            methods = cors_config['allow_methods']
            if not isinstance(methods, list):
                self.errors.append(f"Invalid CORS allow_methods: must be a list")
        
        print(f"✅ CORS configuration validated")
    
    def _validate_rate_limiting_config(self, rate_limiting_config: Dict[str, Any]):
        """Validate rate limiting configuration"""
        required_fields = ['enabled', 'requests_per_minute']
        
        for field in required_fields:
            if field not in rate_limiting_config:
                self.errors.append(f"Missing required field in rate limiting config: {field}")
        
        # Validate requests per minute
        if 'requests_per_minute' in rate_limiting_config:
            requests = rate_limiting_config['requests_per_minute']
            if not isinstance(requests, int) or requests < 0:
                self.errors.append(f"Invalid requests per minute: {requests}")
        
        print(f"✅ Rate limiting configuration validated")
    
    def _validate_environment_variables(self):
        """Validate environment variables"""
        print("🌍 Validating environment variables...")
        
        # Check required environment variables
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "JWT_SECRET"
        ]
        
        for var in required_vars:
            if not os.getenv(var):
                self.errors.append(f"Missing required environment variable: {var}")
            else:
                print(f"✅ Found: {var}")
        
        # Check API keys in production
        if os.getenv("APP_ENV") == "production":
            api_key_vars = ["GLM_API_KEY", "CLAUDE_API_KEY"]
            for var in api_key_vars:
                if not os.getenv(var):
                    self.errors.append(f"Missing API key in production: {var}")
                else:
                    print(f"✅ Found: {var}")
    
    def _check_sensitive_data(self):
        """Check for sensitive data in configuration files"""
        print("🔒 Checking for sensitive data...")
        
        sensitive_patterns = [
            "password",
            "secret",
            "key",
            "token",
            "auth"
        ]
        
        config_files = [
            "config/development.yaml",
            "config/production.yaml"
        ]
        
        for file_path in config_files:
            if Path(file_path).exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                    for pattern in sensitive_patterns:
                        if pattern in content.lower() and "example" not in content.lower():
                            self.warnings.append(f"Potential sensitive data in {file_path}: {pattern}")
        
        if not self.warnings:
            print("✅ No sensitive data detected")
    
    def _report_results(self):
        """Report validation results"""
        print("\n" + "="*50)
        print("VALIDATION RESULTS")
        print("="*50)
        
        if not self.errors and not self.warnings:
            print("🎉 All validations passed!")
            return True
        
        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        return len(self.errors) == 0

def main():
    validator = ConfigValidator()
    
    if validator.validate_all():
        print("\n🎉 Configuration validation successful!")
        sys.exit(0)
    else:
        print("\n❌ Configuration validation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Database Setup

### PostgreSQL Setup

**Database Initialization Script:**
```sql
-- scripts/init_postgres.sql

-- Create database
CREATE DATABASE kyros_prod
    WITH
    OWNER = kyros
    ENCODING = 'UTF8'
    CONNECTION LIMIT = -1;

-- Connect to the database
\c kyros_prod;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schema
CREATE SCHEMA IF NOT EXISTS kyros;

-- Create users table
CREATE TABLE IF NOT EXISTS kyros.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create tasks table
CREATE TABLE IF NOT EXISTS kyros.tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    assignee_role VARCHAR(50),
    created_by UUID REFERENCES kyros.users(id),
    assigned_to UUID,
    deadline TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- Create agent_submissions table
CREATE TABLE IF NOT EXISTS kyros.agent_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES kyros.tasks(id),
    agent_id VARCHAR(255) NOT NULL,
    agent_role VARCHAR(50) NOT NULL,
    model_used VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    estimated_duration INTEGER,
    actual_duration INTEGER,
    cost_usd DECIMAL(10, 4),
    results JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create escalations table
CREATE TABLE IF NOT EXISTS kyros.escalations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES kyros.tasks(id),
    original_model VARCHAR(100) NOT NULL,
    target_model VARCHAR(100) NOT NULL,
    reason TEXT NOT NULL,
    confidence_score DECIMAL(5, 4),
    estimated_cost DECIMAL(10, 4),
    actual_cost DECIMAL(10, 4),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    approved_by UUID REFERENCES kyros.users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create cost_tracking table
CREATE TABLE IF NOT EXISTS kyros.cost_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL,
    model VARCHAR(100) NOT NULL,
    requests INTEGER NOT NULL DEFAULT 0,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd DECIMAL(10, 4) NOT NULL,
    agent_role VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(date, model, agent_role)
);

-- Create audit_log table
CREATE TABLE IF NOT EXISTS kyros.audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    user_id UUID REFERENCES kyros.users(id),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_tasks_status ON kyros.tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON kyros.tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON kyros.tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_assignee_role ON kyros.tasks(assignee_role);
CREATE INDEX IF NOT EXISTS idx_submissions_task_id ON kyros.agent_submissions(task_id);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON kyros.agent_submissions(status);
CREATE INDEX IF NOT EXISTS idx_submissions_agent_role ON kyros.agent_submissions(agent_role);
CREATE INDEX IF NOT EXISTS idx_escalations_task_id ON kyros.escalations(task_id);
CREATE INDEX IF NOT EXISTS idx_escalations_status ON kyros.escalations(status);
CREATE INDEX IF NOT EXISTS idx_cost_tracking_date ON kyros.cost_tracking(date);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON kyros.audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON kyros.audit_log(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON kyros.audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON kyros.audit_log(created_at);

-- Create user for application
CREATE USER kyros_app WITH PASSWORD '${KYROS_APP_PASSWORD}';

-- Grant privileges
GRANT CONNECT ON DATABASE kyros_prod TO kyros_app;
GRANT USAGE ON SCHEMA kyros TO kyros_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA kyros TO kyros_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA kyros TO kyros_app;

-- Create read-only user for monitoring
CREATE USER kyros_readonly WITH PASSWORD '${KYROS_READONLY_PASSWORD}';
GRANT CONNECT ON DATABASE kyros_prod TO kyros_readonly;
GRANT USAGE ON SCHEMA kyros TO kyros_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA kyros TO kyros_readonly;

-- Insert default admin user
INSERT INTO kyros.users (id, email, password_hash, name, role)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'admin@kyros.com',
    crypt('$2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeWUxw6K5mZJ6V7',
    'System Administrator',
    'admin'
) ON CONFLICT (email) DO NOTHING;

-- Insert default roles
INSERT INTO kyros.users (id, email, password_hash, name, role)
VALUES 
    (
        '00000000-0000-0000-0000-000000000002',
        'architect@kyros.com',
        crypt('$2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeWUxw6K5mZJ6V7',
        'System Architect',
        'architect'
    ),
    (
        '00000000-0000-0000-0000-000000000003',
        'orchestrator@kyros.com',
        crypt('$2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeWUxw6K5mZJ6V7',
        'Task Orchestrator',
        'orchestrator'
    ),
    (
        '00000000-0000-0000-0000-000000000004',
        'implementer@kyros.com',
        crypt('$2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeWUxw6K5mZJ6V7',
        'Code Implementer',
        'implementer'
    ),
    (
        '00000000-0000-0000-0000-000000000005',
        'critic@kyros.com',
        crypt('$2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeWUxw6K5mZJ6V7',
        'Code Critic',
        'critic'
    ),
    (
        '00000000-0000-0000-0000-000000000006',
        'integrator@kyros.com',
        crypt('$2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeWUxw6K5mZJ6V7',
        'Integration Specialist',
        'integrator'
    )
ON CONFLICT (email) DO NOTHING;

-- Create functions for cost tracking
CREATE OR REPLACE FUNCTION kyros.track_model_usage(
    p_model VARCHAR(100),
    p_input_tokens INTEGER,
    p_output_tokens INTEGER,
    p_cost_usd DECIMAL(10, 4),
    p_agent_role VARCHAR(50)
) RETURNS VOID AS $$
DECLARE
    v_today DATE := CURRENT_DATE;
BEGIN
    INSERT INTO kyros.cost_tracking (
        date,
        model,
        requests,
        input_tokens,
        output_tokens,
        cost_usd,
        agent_role
    ) VALUES (
        v_today,
        p_model,
        1,
        p_input_tokens,
        p_output_tokens,
        p_cost_usd,
        p_agent_role
    ) ON CONFLICT (date, model, agent_role) DO UPDATE SET
            requests = cost_tracking.requests + 1,
            input_tokens = cost_tracking.input_tokens + p_input_tokens,
            output_tokens = cost_tracking.output_tokens + p_output_tokens,
            cost_usd = cost_tracking.cost_usd + p_cost_usd;
END;
$$ LANGUAGE plpgsql;

-- Create function for audit logging
CREATE OR REPLACE FUNCTION kyros.log_audit(
    p_action VARCHAR(100),
    p_resource_type VARCHAR(50),
    p_resource_id UUID,
    p_user_id UUID,
    p_details JSONB,
    p_ip_address INET,
    p_user_agent TEXT
) RETURNS VOID AS $$
BEGIN
    INSERT INTO kyros.audit_log (
        action,
        resource_type,
        resource_id,
        user_id,
        details,
        ip_address,
        user_agent,
        created_at
    ) VALUES (
        p_action,
        p_resource_type,
        p_resource_id,
        p_user_id,
        p_details,
        p_ip_address,
        p_user_agent,
        NOW()
    );
END;
$$ LANGUAGE plpgsql;

-- Create view for task statistics
CREATE OR REPLACE VIEW kyros.task_statistics AS
SELECT
    DATE_TRUNC('day', created_at) AS date,
    status,
    type,
    assignee_role,
    COUNT(*) AS task_count,
    AVG(EXTRACT(EPOCH FROM (completed_at - created_at))/3600) AS avg_duration_hours
FROM kyros.tasks
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', created_at), status, type, assignee_role
ORDER BY date DESC;

-- Create view for cost analysis
CREATE OR REPLACE VIEW kyros.cost_analysis AS
SELECT
    DATE_TRUNC('day', date) AS date,
    model,
    agent_role,
    SUM(requests) AS total_requests,
    SUM(input_tokens) AS total_input_tokens,
    SUM(output_tokens) AS total_output_tokens,
    SUM(cost_usd) AS total_cost,
    AVG(cost_usd) AS avg_cost_per_request
FROM kyros.cost_tracking
WHERE date >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', date), model, agent_role
ORDER BY date DESC;

-- Set up automatic vacuuming
ALTER TABLE kyros.users SET (autovacuum_enabled = true, autovacuum_vacuum_threshold = 1000, autovacuum_analyze_threshold = 500);
ALTER TABLE kyros.tasks SET (autovacuum_enabled = true, autovacuum_vacuum_threshold = 1000, autovacuum_analyze_threshold = 500);
ALTER TABLE kyros.agent_submissions SET (autovacuum_enabled = true, autovacuum_vacuum_threshold = 1000, autovacuum_analyze_threshold = 500);
ALTER TABLE kyros.escalations SET (autovacuum_enabled = true, autovacuum_vacuum_threshold = 1000, autovacuum_analyze_threshold = 500);
ALTER TABLE kyros.cost_tracking SET (autovacuum_enabled = true, autovacuum_vacuum_threshold = 1000, autovacuum_analyze_threshold = 500);
ALTER TABLE kyros.audit_log SET (autovacuum_enabled = true, autovacuum_vacuum_threshold = 1000, autovacuum_analyze_threshold = 500);

-- Set up tablespace for large tables (optional)
-- CREATE TABLESPACE kyros_data LOCATION '/var/lib/postgresql/kyros_data';
-- ALTER TABLE kyros.audit_log SET TABLESPACE kyros_data;
-- ALTER TABLE kyros.cost_tracking SET TABLESPACE kyros_data;

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION kyros.track_model_usage TO kyros_app;
GRANT EXECUTE ON FUNCTION kyros.log_audit TO kyros_app;
GRANT SELECT ON kyros.task_statistics TO kyros_app;
GRANT SELECT ON kyros.cost_analysis TO kyros_app;

-- Set up default privileges for new tables
ALTER DEFAULT PRIVILEGES IN SCHEMA kyros
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO kyros_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA kyros
    GRANT USAGE, SELECT ON SEQUENCES TO kyros_app;

-- Database information
SELECT current_database() AS database_name,
       version() AS version,
       setting AS timezone
FROM pg_settings
WHERE name = 'TimeZone';

-- Table information
SELECT table_name,
       table_type,
       (SELECT pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM information_schema.tables
WHERE table_schema = 'kyros'
ORDER BY table_name;

-- Index information
SELECT indexname,
       tablename,
       indexdef
FROM pg_indexes
WHERE schemaname = 'kyros'
ORDER BY tablename, indexname;

-- User and role information
SELECT usename AS username,
       usecreatedb AS can_create_db,
       usesuper AS is_superuser,
       usecreaterole AS can_create_role,
       passwd AS password_hash
FROM pg_catalog.pg_user
ORDER BY usename;

-- Privilege information
SELECT grantee,
       privilege_type,
       table_name,
       table_schema
FROM information_schema.role_table_grants
WHERE table_schema = 'kyros'
ORDER BY grantee, table_name;

-- Vacuum and analyze statistics
VACUUM ANALYZE kyros.users;
VACMUM ANALYZE kyros.tasks;
VACMUM ANALYZE kyros.agent_submissions;
VACMUM ANALYZE kyros.escalations;
VACMUM ANALYZE kyros.cost_tracking;
VACMUM ANALYZE kyros.audit_log;

-- Database statistics
SELECT schemaname,
       tablename,
       seq_scan,
       seq_tup_read,
       idx_scan,
       idx_tup_fetch,
       n_tup_ins,
       n_tup_upd,
       n_tup_del,
       last_vacuum,
       last_autovacuum,
       last_analyze,
       last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'kyros'
ORDER BY tablename;

-- Connection information
SELECT datname,
       numbackends,
       xact_commit,
       xact_rollback,
      blks_read,
      blks_hit
FROM pg_stat_database
WHERE datname = 'kyros_prod';

-- Extension information
SELECT extname,
       extversion,
       nspname AS schema_name
FROM pg_extension
JOIN pg_namespace ON pg_extension.extnamespace = pg_namespace.oid
ORDER BY extname;

-- Configuration settings
SELECT name,
       setting,
       unit,
       category,
       short_desc,
       extra_desc,
       context,
       vartype,
    