import pytest
from unittest.mock import AsyncMock, patch
from services.orchestrator.repositories.jobs import get_jobs, create_job, add_event
from services.orchestrator.models import Job, Event


@pytest.mark.asyncio
async def test_get_jobs_empty():
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_scalars = AsyncMock(return_value=[])
    mock_result.scalars = mock_scalars
    mock_session.execute.return_value = mock_result
    jobs = await get_jobs(mock_session)
    assert len(jobs) == 0


@pytest.mark.asyncio
async def test_create_job_invalid_name():
    mock_session = AsyncMock()
    with patch.object(
        mock_session,
        'commit',
        side_effect=ValueError("Invalid name")
    ):
        with pytest.raises(ValueError):
            await create_job(mock_session, "")


@pytest.mark.asyncio
async def test_add_event_invalid_payload():
    mock_session = AsyncMock()
    with patch.object(
        mock_session,
        'commit',
        side_effect=ValueError("Invalid payload")
    ):
        with pytest.raises(ValueError):
            await add_event(mock_session, "test", None)
