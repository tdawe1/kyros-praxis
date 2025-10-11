import pytest
from fastapi.testclient import TestClient

from services.orchestrator.auth import pwd_context
from services.orchestrator.database import get_db
from services.orchestrator.main import app
from services.orchestrator.models import Base, User
from services.orchestrator.utils.etag import generate_etag
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test function."""
    import tempfile
    import os

    # Create a temporary file for the database
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_file.close()

    try:
        # Create sync engine
        engine = create_engine(
            f"sqlite:///{db_file.name}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Create async engine
        async_engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_file.name}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        TestingAsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

        # Create all tables on sync engine
        Base.metadata.create_all(bind=engine)

        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()

        async def override_get_db_session():
            async with TestingAsyncSessionLocal() as session:
                yield session

        # Override both sync and async dependencies
        app.dependency_overrides[get_db] = override_get_db
        from services.orchestrator.database import get_db_session
        app.dependency_overrides[get_db_session] = override_get_db_session

        yield TestingSessionLocal()

        # Clean up
        Base.metadata.drop_all(bind=engine)
    finally:
        # Clean up the temporary file
        try:
            os.unlink(db_file.name)
        except (OSError, FileNotFoundError):
            pass
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    """Create a test client with test database."""
    return TestClient(app)


def test_create_job_contract(client, test_db):
    # seed user and login
    if not test_db.query(User).filter(User.username == "jobsuser").first():
        user = User(
            username="jobsuser", email="jobs@example.com", password_hash=pwd_context.hash("password")
        )
        test_db.add(user)
        test_db.commit()

    login = client.post(
        "/auth/login", json={"username": "jobsuser", "password": "password"}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    response = client.post(
        "/api/v1/jobs",
        json={"title": "test"},
        headers={"Authorization": f"Bearer {token}", "X-API-Key": "ci-key"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "status" in data

    expected_etag = generate_etag(data)
    assert response.headers["ETag"] == expected_etag


def test_list_jobs_contract(client, test_db):
    # Ensure user exists (created by previous test or create if not exists)
    if not test_db.query(User).filter(User.username == "jobsuser").first():
        user = User(
            username="jobsuser", email="jobs@example.com", password_hash=pwd_context.hash("password")
        )
        test_db.add(user)
        test_db.commit()

    login = client.post(
        "/auth/login", json={"username": "jobsuser", "password": "password"}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    response = client.get(
        "/api/v1/jobs", headers={"Authorization": f"Bearer {token}", "X-API-Key": "ci-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)  # Should return a list of jobs

    expected_etag = generate_etag(data)
    assert response.headers["ETag"] == expected_etag
