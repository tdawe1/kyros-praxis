#!/usr/bin/env bash

set -e
set -x

echo "Running prestart script..."

# Wait for the database to be ready
echo "Waiting for database..."
python scripts/backend_pre_start.py

# Run Alembic migrations for orchestrator service
echo "Running orchestrator migrations..."
cd services/orchestrator
alembic upgrade head
cd ../..

# Run Alembic migrations for service-registry
echo "Running service-registry migrations..."
cd packages/service-registry
alembic upgrade head
cd ../..

# Create initial data/superuser if enabled
if [ "${ENABLE_SEED}" = "true" ] || [ "${FIRST_SUPERUSER}" != "" ]; then
    echo "Creating initial data..."
    python scripts/initial_data.py
fi

echo "Prestart script completed successfully!"