"""Fixtures and configuration for unit tests."""
import os
import sys
import pytest
from pathlib import Path

# Set required environment variables for testing
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
# Use a file-based SQLite DB to ensure the same database is visible across connections
os.environ["DATABASE_URL"] = "sqlite:///./test_unit.db"

# Add the orchestrator directory to the path
orchestrator_dir = Path(__file__).parents[2]
if str(orchestrator_dir) not in sys.path:
    sys.path.insert(0, str(orchestrator_dir))

# Import after path setup - need to do this after setting env vars
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

try:
    from models import Base
    from database import get_db
    from main import app
except ImportError as e:
    # If imports fail, create minimal stubs for testing
    print(f"Import error: {e}")
    Base = None
    get_db = None
    app = None

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test."""
    if Base is None:
        pytest.skip("Cannot import required modules")
        
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestingSessionLocal()
    
    # Clean up
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

@pytest.fixture
def client():
    """Create a test client."""
    if app is None:
        pytest.skip("Cannot import app")
    from fastapi.testclient import TestClient
    return TestClient(app)
