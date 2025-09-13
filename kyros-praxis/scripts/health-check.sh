#!/bin/bash

# Health check script for monitoring
# Usage: ./scripts/health-check.sh [service]

SERVICE=${1:-all}
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0"])" && pwd)

echo "🔍 Running health checks for: $SERVICE"

case "$SERVICE" in
    "frontend")
        echo "📱 Checking frontend..."
        curl -f http://localhost:3001/api/health || exit 1
        ;;
    "backend")
        echo "🔧 Checking backend..."
        curl -f http://localhost:8000/api/v1/utils/health-check || exit 1
        ;;
    "daemon")
        echo "🖥️ Checking terminal daemon..."
        curl -f http://localhost:8787/health || exit 1
        ;;
    "database")
        echo "🗄️ Checking database..."
        python -c "
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
conn.cursor().execute('SELECT 1')
conn.close()
" || exit 1
        ;;
    "redis")
        echo "🔴 Checking Redis..."
        redis-cli ping || exit 1
        ;;
    "qdrant")
        echo "🔍 Checking Qdrant..."
        curl -f http://localhost:6333/ || exit 1
        ;;
    "all")
        echo "🔄 Running all health checks..."
        ./scripts/health-check.sh frontend
        ./scripts/health-check.sh backend
        ./scripts/health-check.sh daemon
        ./scripts/health-check.sh database
        ./scripts/health-check.sh redis
        ./scripts/health-check.sh qdrant
        ;;
    *)
        echo "❌ Unknown service: $SERVICE"
        echo "Usage: $0 [frontend|backend|daemon|database|redis|qdrant|all]"
        exit 1
        ;;
esac

echo "✅ Health checks passed for $SERVICE"