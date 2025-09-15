import pytest
import pytest_asyncio
from services.orchestrator.models import Base, Event, Job
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


@pytest_asyncio.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_job_model(async_session):
    job = Job(name="Test Job")
    async_session.add(job)
    await async_session.commit()
    await async_session.refresh(job)
    assert job.name == "Test Job"
    assert job.status == "pending"


@pytest.mark.asyncio
async def test_event_model(async_session):
    event = Event(type="test", payload={"key": "value"})
    async_session.add(event)
    await async_session.commit()
    await async_session.refresh(event)
    assert event.type == "test"
    assert event.payload == {"key": "value"}
