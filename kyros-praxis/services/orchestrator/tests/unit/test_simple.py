"""Simple unit tests that don't require full app import."""
import os
import sys
from pathlib import Path

# Set up environment
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Add path
sys.path.insert(0, str(Path(__file__).parents[2]))

def test_environment_setup():
    """Test that environment variables are set correctly."""
    assert os.environ.get("SECRET_KEY") == "test-secret-key"
    assert os.environ.get("DATABASE_URL") == "sqlite:///:memory:"

def test_models_import():
    """Test that models can be imported."""
    try:
        from models import Base, User, Task, Job, Event
        assert Base is not None
        assert User.__tablename__ == "users"
        assert Task.__tablename__ == "tasks"
        assert Job.__tablename__ == "jobs"
        assert Event.__tablename__ == "events"
    except ImportError as e:
        print(f"Import error: {e}")
        assert False, "Could not import models"

def test_database_config():
    """Test database configuration."""
    try:
        from database import DATABASE_URL, get_db
        assert DATABASE_URL == "sqlite:///:memory:"
        assert get_db is not None
    except ImportError as e:
        print(f"Import error: {e}")
        assert False, "Could not import database"

def test_auth_functions():
    """Test auth utility functions."""
    try:
        from auth import verify_password, pwd_context
        
        password = "testpassword123"
        # Use pwd_context directly since get_password_hash is not exported
        hashed = pwd_context.hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    except ImportError as e:
        print(f"Import error: {e}")
        assert False, "Could not import auth"

def test_create_access_token():
    """Test JWT token creation."""
    try:
        from auth import create_access_token
        from datetime import timedelta
        
        token = create_access_token(
            data={"sub": "test@example.com"},
            expires_delta=timedelta(minutes=15)
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    except ImportError as e:
        print(f"Import error: {e}")
        assert False, "Could not import auth functions"

def test_model_creation():
    """Test creating model instances."""
    try:
        from models import User, Task
        from uuid import uuid4
        
        # Create user instance
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            password_hash="hashed_password"
        )
        assert user.email == "test@example.com"
        
        # Create task instance
        task = Task(
            id=str(uuid4()),
            title="Test Task",
            description="A test task",
            version=1
        )
        assert task.title == "Test Task"
        assert task.version == 1
        
    except ImportError as e:
        print(f"Import error: {e}")
        assert False, "Could not create model instances"

if __name__ == "__main__":
    # Run tests
    import pytest
    pytest.main([__file__, "-v"])