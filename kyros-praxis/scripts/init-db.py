#!/usr/bin/env python3
"""
Initialize the database with tables
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from sqlalchemy.ext.asyncio import create_async_engine
from services.orchestrator.models import Base
from services.orchestrator.app.core.config import settings

async def init_database():
    """Initialize database tables"""
    # Use the configured database URL
    database_url = settings.SQLALCHEMY_DATABASE_URI

    # Convert to async if it's SQLite
    if isinstance(database_url, str) and database_url.startswith("sqlite:///"):
        database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    elif hasattr(database_url, 'startswith') and callable(database_url.startswith) and database_url.startswith("sqlite:///"):
        database_url = str(database_url).replace("sqlite:///", "sqlite+aiosqlite:///")

    print(f"Initializing database: {database_url}")

    # Create async engine
    engine = create_async_engine(
        str(database_url),
        echo=False,  # Set to True for SQL debugging
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Database initialized successfully")

    # Dispose engine
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_database())