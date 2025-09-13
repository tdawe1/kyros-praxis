#!/bin/bash

# CI Testing Script for kyros-praxis
# Usage: ./scripts/ci/test.sh [unit|integration|e2e]

set -e

TYPE=${1:-unit}
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

echo "🧪 Running $TYPE tests..."

if [[ "$TYPE" == "unit" ]]; then
    echo "📦 Running unit tests..."
    
    # Frontend unit tests
    cd "$PROJECT_ROOT/services/console"
    npm test -- --watchAll=false --passWithNoTests
    
    # Backend unit tests
    cd "$PROJECT_ROOT/services/orchestrator"
    python -m pytest tests/unit/ -v
    
elif [[ "$TYPE" == "integration" ]]; then
    echo "🔗 Running integration tests..."
    
    # Start test database
    cd "$PROJECT_ROOT"
    docker-compose -f docker-compose.test.yml up -d postgres qdrant redis
    
    # Wait for services to be ready
    sleep 10
    
    # Run integration tests
    cd "$PROJECT_ROOT/services/orchestrator"
    python -m pytest tests/integration/ -v
    
    # Contract tests
    cd "$PROJECT_ROOT/services/console"
    npm run api:check
    
    # Cleanup
    cd "$PROJECT_ROOT"
    docker-compose -f docker-compose.test.yml down -v
    
elif [[ "$TYPE" == "e2e" ]]; then
    echo "🌐 Running E2E tests..."
    
    # Start full test stack
    cd "$PROJECT_ROOT"
    docker-compose -f docker-compose.test.yml up -d
    
    # Wait for all services
    sleep 30
    
    # Run Playwright tests
    cd "$PROJECT_ROOT/services/console"
    npx playwright test
    
    # Cleanup
    cd "$PROJECT_ROOT"
    docker-compose -f docker-compose.test.yml down -v
    
else
    echo "❌ Unknown test type: $TYPE"
    echo "Usage: $0 [unit|integration|e2e]"
    exit 1
fi

echo "✅ $TYPE tests completed successfully"