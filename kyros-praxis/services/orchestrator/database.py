"""
Database configuration and session management for the Kyros Orchestrator service.

This module sets up both synchronous and asynchronous database connections using SQLAlchemy,
configures session factories, and provides dependency-injectable database session generators
for use in FastAPI endpoints.

The module supports configuration via environment variables and ensures proper cleanup
of database sessions.

MODULE RESPONSIBILITIES:
------------------------
1. Database Engine Configuration:
   - Creates synchronous and asynchronous SQLAlchemy engines
   - Configures database URLs from environment variables
   - Sets up connection parameters for different database types (SQLite, PostgreSQL, etc.)

2. Session Management:
   - Creates session factories for both sync and async operations
   - Provides FastAPI dependency-injectable session generators
   - Ensures proper session cleanup and resource management

3. Model Integration:
   - Integrates with models.py to ensure database tables exist
   - Supports both synchronous and asynchronous database operations

4. Configuration Management:
   - Loads database URLs from environment variables
   - Supports SQL query logging for debugging
   - Handles database-specific connection parameters

DATABASE ARCHITECTURE:
----------------------
The orchestrator uses a layered approach to database access:

1. Engine Layer:
   - Synchronous engine (engine) for traditional blocking operations
   - Asynchronous engine (async_engine) for async operations

2. Session Layer:
   - Synchronous session factory (SessionLocal) for blocking operations
   - Asynchronous session factory (AsyncSessionLocal) for async operations

3. Dependency Layer:
   - get_db() for synchronous FastAPI endpoint dependencies
   - get_db_session() for asynchronous FastAPI endpoint dependencies

INTEGRATION WITH OTHER MODULES:
-------------------------------
- main.py: Uses get_db dependency for health checks and database connectivity
- models.py: Creates tables and defines ORM models
- auth.py: Uses get_db dependency for user authentication and retrieval

USAGE EXAMPLES:
---------------
Synchronous database access in FastAPI endpoints:
    def get_users(db = Depends(get_db)):
        return db.query(User).all()

Asynchronous database access in FastAPI endpoints:
    async def get_users(db = Depends(get_db_session)):
        result = await db.execute(select(User))
        return result.scalars().all()

ENVIRONMENT VARIABLES:
----------------------
- DATABASE_URL: Synchronous database connection URL (default: sqlite:///orchestrator.db)
- ASYNC_DATABASE_URL: Asynchronous database connection URL (default: sqlite+aiosqlite:///orchestrator.db)
- SQL_ECHO: Enable SQL query logging (default: false)

See Also:
--------
- models.py: Database models for jobs, events, tasks, and users
- main.py: FastAPI application that uses database dependencies
- auth.py: Authentication module that depends on database access
"""

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure a stable absolute path for the local SQLite file regardless of CWD
_db_path = Path(__file__).resolve().parent / "orchestrator.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_db_path}")
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL", f"sqlite+aiosqlite:///{_db_path}")

# Enable SQL query logging based on environment variable
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() in {"1", "true", "yes"}

# Configure database connection parameters
_sync_kwargs = {"echo": SQL_ECHO}
_async_kwargs = {"echo": SQL_ECHO}
if DATABASE_URL.startswith("sqlite:///"):
    _sync_kwargs["connect_args"] = {"check_same_thread": False}
if ASYNC_DATABASE_URL.startswith("sqlite+aiosqlite"):
    _async_kwargs["connect_args"] = {"check_same_thread": False}

# Create synchronous and asynchronous database engines
engine = create_engine(DATABASE_URL, **_sync_kwargs)
async_engine = create_async_engine(ASYNC_DATABASE_URL, **_async_kwargs)

# Create session factories for both sync and async operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# Ensure tables exist on import to support test seeding prior to app startup
try:
    from .models import Base  # type: ignore

    Base.metadata.create_all(bind=engine)
except Exception:
    pass


def get_db():
    """
    FastAPI dependency for providing a synchronous database session.
    
    Creates a database session that is automatically closed when the request ends.
    This function is used as a dependency in FastAPI endpoints that require
    synchronous database access.
    
    Yields:
        Session: A SQLAlchemy database session
        
    Example:
        def get_users(db = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_db_session():
    """
    FastAPI dependency for providing an asynchronous database session.
    
    Creates an asynchronous database session that is automatically closed when
    the request ends. This function is used as a dependency in FastAPI endpoints
    that require asynchronous database access.
    
    Yields:
        AsyncSession: An asynchronous SQLAlchemy database session
        
    Example:
        async def get_users(db = Depends(get_db_session)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        yield session
