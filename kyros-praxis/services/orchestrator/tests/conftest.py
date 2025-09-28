import os
import sys
from pathlib import Path

# Set up test environment BEFORE any imports
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("API_KEYS", "ci-key,test-key")
# Use file-based SQLite for tests to share between sync and async
test_db_path = Path(__file__).resolve().parent / "test.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{test_db_path}")
os.environ.setdefault("ASYNC_DATABASE_URL", f"sqlite+aiosqlite:///{test_db_path}")

# Set up test-friendly events file paths to avoid PermissionError
import tempfile
test_events_dir = Path(tempfile.mkdtemp()) / "events"
os.environ.setdefault("EVENTS_DIR", str(test_events_dir))
os.environ.setdefault("EVENTS_FILE", "events.jsonl")

# Ensure 'services' within kyros-praxis is importable as a top-level package
repo_root = Path(__file__).resolve().parents[3]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import pytest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from services.orchestrator.models import Base

# Import pytest_asyncio for async fixtures
try:
    import pytest_asyncio
except ImportError:
    pytest_asyncio = None


@pytest.fixture(scope="session")
def engine():
    """Create test database engines with SQLite file database."""
    import asyncio

    # Create async engine with specified parameters
    async_engine = create_async_engine(
        f"sqlite+aiosqlite:///{test_db_path}",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Create schema via async engine
    asyncio.run(create_schema(async_engine))

    # Also create sync engine for compatibility
    sync_engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    yield sync_engine, async_engine

    # Cleanup
    Base.metadata.drop_all(bind=sync_engine)
    asyncio.run(async_engine.dispose())
    test_db_path.unlink(missing_ok=True)


async def create_schema(async_engine):
    """Create schema via async engine."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="session")
def tables(engine):
    """Ensure tables are created (schema already created in engine fixture)."""
    # Tables are already created in the engine fixture
    yield


@pytest.fixture
def db_session(engine, tables):
    """Create a test database session."""
    sync_engine, _ = engine
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
async def async_db_session(engine, tables):
    """Create a test async database session."""
    _, async_engine = engine
    # Set up AsyncSessionLocal
    AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def async_session(engine, tables):
    """Async fixture for AsyncSessionLocal (compatible with pytest_asyncio)."""
    _, async_engine = engine
    AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
def override_get_db(db_session):
    """Override the get_db dependency for FastAPI tests."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass
    return _override_get_db


@pytest.fixture
def override_get_db_async(async_db_session):
    """Override the get_db_session dependency for FastAPI async tests."""
    async def _override_get_db_async():
        yield async_db_session
    return _override_get_db_async


@pytest.fixture(autouse=True)
def setup_database(engine, tables):
    """Ensure database is set up for all tests and override database module."""
    sync_engine, async_engine = engine

    # Monkey patch the database module to use our test database
    import services.orchestrator.database as db_module
    db_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    db_module.AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)
    # This fixture runs automatically for all tests
    pass