#!/bin/bash

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root!"
   exit 1
fi

# Check prerequisites
print_status "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running. Please start Docker."
    exit 1
fi

print_success "Prerequisites check passed"

# Environment setup
print_status "Setting up environment..."

# Check if .env file exists
if [ ! -f .env ]; then
    if [ -f .env.template ]; then
        print_warning ".env file not found. Creating from template..."
        cp .env.template .env
        
        # Generate secure secrets
        print_status "Generating secure secrets..."
        JWT_SECRET=$(openssl rand -base64 32)
        CSRF_SECRET=$(openssl rand -base64 32)
        SESSION_SECRET=$(openssl rand -base64 32)
        NEXTAUTH_SECRET=$(openssl rand -base64 32)
        POSTGRES_PASSWORD=$(openssl rand -base64 16)
        REDIS_PASSWORD=$(openssl rand -base64 16)
        GRAFANA_PASSWORD=$(openssl rand -base64 16)
        
        # Update .env file with generated secrets
        sed -i "s|JWT_SECRET=.*|JWT_SECRET=$JWT_SECRET|" .env
        sed -i "s|CSRF_SECRET=.*|CSRF_SECRET=$CSRF_SECRET|" .env
        sed -i "s|SESSION_SECRET=.*|SESSION_SECRET=$SESSION_SECRET|" .env
        sed -i "s|NEXTAUTH_SECRET=.*|NEXTAUTH_SECRET=$NEXTAUTH_SECRET|" .env
        sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$POSTGRES_PASSWORD|" .env
        sed -i "s|REDIS_PASSWORD=.*|REDIS_PASSWORD=$REDIS_PASSWORD|" .env
        sed -i "s|GRAFANA_PASSWORD=.*|GRAFANA_PASSWORD=$GRAFANA_PASSWORD|" .env
        
        print_success "Secrets generated and saved to .env"
        print_warning "Please review and update .env file with your specific configuration"
    else
        print_error ".env file not found and no template available"
        exit 1
    fi
else
    print_success "Environment file found"
fi

# Load environment variables
source .env

# Clean up old containers and volumes (optional)
if [ "$1" == "--clean" ]; then
    print_warning "Cleaning up old containers and volumes..."
    docker-compose -f docker-compose.production.yml down -v
    print_success "Cleanup complete"
fi

# Build Docker images
print_status "Building Docker images..."

# Build backend
print_status "Building orchestrator service..."
docker-compose -f docker-compose.production.yml build orchestrator

# Build frontend
print_status "Building console service..."
docker-compose -f docker-compose.production.yml build console

print_success "Docker images built successfully"

# Database initialization
print_status "Initializing database..."

# Start only database first
docker-compose -f docker-compose.production.yml up -d postgres
sleep 5  # Wait for postgres to be ready

# Check if database is ready
MAX_RETRIES=30
RETRY_COUNT=0
while ! docker-compose -f docker-compose.production.yml exec -T postgres pg_isready -U ${POSTGRES_USER:-kyros_user} &> /dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -gt $MAX_RETRIES ]; then
        print_error "Database failed to start after $MAX_RETRIES attempts"
        exit 1
    fi
    print_status "Waiting for database to be ready... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

print_success "Database is ready"

# Run database migrations
print_status "Running database migrations..."
docker-compose -f docker-compose.production.yml run --rm orchestrator alembic upgrade head || true

# Start all services
print_status "Starting all services..."
docker-compose -f docker-compose.production.yml up -d

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."

# Function to check service health
check_service_health() {
    local service=$1
    local url=$2
    local max_retries=30
    local retry_count=0
    
    while true; do
        if curl -f -s "$url" > /dev/null; then
            print_success "$service is healthy"
            return 0
        fi
        
        retry_count=$((retry_count + 1))
        if [ $retry_count -gt $max_retries ]; then
            print_error "$service failed health check after $max_retries attempts"
            return 1
        fi
        
        print_status "Waiting for $service... ($retry_count/$max_retries)"
        sleep 3
    done
}

# Check each service
check_service_health "Orchestrator API" "http://localhost:8000/healthz"
check_service_health "Console Frontend" "http://localhost:3000"
check_service_health "Prometheus" "http://localhost:9090/-/healthy"
check_service_health "Grafana" "http://localhost:3001/api/health"

# Run smoke tests
print_status "Running smoke tests..."

# Test API endpoint
if curl -f -s http://localhost:8000/api/v1/health-check > /dev/null; then
    print_success "API health check passed"
else
    print_warning "API health check failed - service may still be starting"
fi

# Test frontend
if curl -f -s http://localhost:3000 | grep -q "Kyros"; then
    print_success "Frontend is serving content"
else
    print_warning "Frontend check failed - service may still be starting"
fi

# Display service status
print_status "Service Status:"
docker-compose -f docker-compose.production.yml ps

# Display access URLs
echo ""
print_success "🚀 Kyros Praxis is running in production mode!"
echo ""
echo "Access URLs:"
echo "  Frontend:    http://localhost:3000"
echo "  API:         http://localhost:8000"
echo "  API Docs:    http://localhost:8000/docs"
echo "  Prometheus:  http://localhost:9090"
echo "  Grafana:     http://localhost:3001 (admin / ${GRAFANA_PASSWORD:-admin})"
echo ""
echo "Database:"
echo "  PostgreSQL:  localhost:5432 (${POSTGRES_USER:-kyros_user} / [password in .env])"
echo "  Redis:       localhost:6379"
echo ""
echo "Useful commands:"
echo "  View logs:         docker-compose -f docker-compose.production.yml logs -f [service]"
echo "  Stop all:          docker-compose -f docker-compose.production.yml down"
echo "  Restart service:   docker-compose -f docker-compose.production.yml restart [service]"
echo "  View metrics:      Open http://localhost:3001 (Grafana)"
echo ""

# Monitor logs (optional)
if [ "$1" == "--logs" ] || [ "$2" == "--logs" ]; then
    print_status "Following logs (Ctrl+C to exit)..."
    docker-compose -f docker-compose.production.yml logs -f
fi

print_success "Production launch complete!"