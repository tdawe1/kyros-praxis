#!/bin/bash

# Database migration script
# Usage: ./scripts/migrate.sh [up|down|revision]

set -e

ACTION=${1:-up}
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

echo "🗄️ Running database migration: $ACTION"

cd "$PROJECT_ROOT/services/orchestrator"

case "$ACTION" in
    "up")
        python -m alembic upgrade head
        echo "✅ Migrated to latest version"
        ;;
    "down")
        python -m alembic downgrade -1
        echo "✅ Reverted last migration"
        ;;
    "revision")
        python -m alembic revision --autogenerate -m "${2:-migration}"
        echo "✅ Created new migration"
        ;;
    "status")
        python -m alembic current
        python -m alembic history
        ;;
    *)
        echo "❌ Unknown action: $ACTION"
        echo "Usage: $0 [up|down|revision|status]"
        exit 1
        ;;
esac