import os
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

TEST_DB_URL = os.getenv("TEST_DATABASE_URL") or "postgresql+asyncpg://kyros:kyros@localhost:5432/kyros_test"
os.environ.setdefault("DATABASE_URL", TEST_DB_URL)

from app.main import app  # noqa: E402
from app.db.session import AsyncSessionLocal, engine  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
    command.upgrade(cfg, "head")
    yield
    if "kyros_test" in os.environ["DATABASE_URL"]:
        command.downgrade(cfg, "base")


@pytest_asyncio.fixture
async def db_cleanup(apply_migrations):
    await engine.dispose()
    async with AsyncSessionLocal() as session:
        # Truncate all tables including users (added for auth tests)
        await session.execute(text("TRUNCATE TABLE crew_events, crew_runs, users RESTART IDENTITY CASCADE"))
        await session.commit()
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
