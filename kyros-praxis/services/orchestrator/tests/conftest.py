import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from services.orchestrator.models import Base, User
from services.orchestrator.auth import pwd_context
import pytest


@pytest.fixture(scope="function")
def sync_override_get_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=engine
    )

    def test_get_db():
        db = TestingSessionLocal()
        user = User(
            email="test@example.com", 
            password_hash=pwd_context.hash("password")
        )
        db.add(user)
        db.commit()
        yield db
        db.close()

    return test_get_db


@pytest.fixture(scope="function")
def async_override_get_db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async def test_get_db_session():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with AsyncSession(engine) as session:
            user = User(
                email="jobs@example.com", 
                password_hash=pwd_context.hash("password")
            )
            session.add(user)
            await session.commit()
            yield session

    return test_get_db_session

# Ensure 'services' within kyros-praxis is importable as a top-level package
repo_root = Path(__file__).resolve().parents[3]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

