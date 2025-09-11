#!/bin/bash

set -e

echo "Setting up Kyros Praxis development environment..."

# Setup root .env if it doesn't exist
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo ".env copied from .env.example"
    else
        echo "Warning: .env.example not found, create it manually."
    fi
else
    echo ".env already exists"
fi

# Backend setup
echo "Setting up backend in services/orchestrator..."
cd services/orchestrator

if [ ! -d .venv ]; then
    echo "Creating Python virtual environment..."
    uv venv
else
    echo "Python virtual environment already exists"
fi

source .venv/bin/activate

if [ -f requirements.txt ]; then
    echo "Installing backend dependencies..."
    uv pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found in services/orchestrator"
fi

cd ..

# Frontend setup
echo "Setting up frontend in services/console..."
cd console

if [ ! -d node_modules ]; then
    echo "Installing frontend dependencies..."
    npm install
else
    echo "Frontend dependencies already installed"
fi

cd ..

# Database migrations (assume DB is set up if alembic.ini exists)
if [ -f orchestrator/alembic.ini ]; then
    echo "Running database migrations..."
    cd services/orchestrator
    alembic upgrade head
    cd ..
else
    echo "Skipping DB migrations: alembic.ini not found in orchestrator"
fi

# Instructions for starting services
echo ""
echo "Setup complete! Next steps:"
echo "1. Start database and Redis (if using Docker Compose):"
echo "   docker-compose up -d postgres"
echo ""
echo "2. To start the backend (services/orchestrator):"
if [ -f scripts/start-backend.sh ]; then
    echo "   scripts/start-backend.sh"
else
    echo "   cd services/orchestrator && source .venv/bin/activate && uvicorn main:app --reload --port 8000"
fi
echo ""
echo "3. To start the frontend (services/console):"
if [ -f scripts/start-frontend.sh ]; then
    echo "   scripts/start-frontend.sh"
else
    echo "   cd services/console && npm run dev"
fi
echo ""
echo "Note: Ensure Docker Compose is configured for Postgres/Redis if using external services."