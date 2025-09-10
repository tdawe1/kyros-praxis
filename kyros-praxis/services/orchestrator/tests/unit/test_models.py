import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from services.orchestrator.models import Job, Event, Base


@pytest.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        yield AsyncSession(conn)
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_job_model(async_session):
    job = Job(name="Test Job")
    async with async_session as session:
        session.add(job)
        await session.commit()
        assert job.name == "Test Job"
        assert job.status == "pending"


@pytest.mark.asyncio
async def test_event_model(async_session):
    event = Event(type="test", payload={"key": "value"})
    async with async_session as session:
        session.add(event)
        await session.commit()
        assert event.type == "test"
        assert event.payload == {"key": "value"}
