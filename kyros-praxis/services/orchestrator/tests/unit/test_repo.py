from unittest.mock import AsyncMock, Mock

import pytest
from services.orchestrator.repositories.jobs import add_event, create_job, get_jobs
from services.orchestrator.tests.utils.sqlalchemy_stubs import create_result_stub


@pytest.mark.asyncio
async def test_get_jobs_empty():
    mock_session = Mock()
    mock_result = create_result_stub([])
    mock_session.execute = AsyncMock(return_value=mock_result)
    jobs = await get_jobs(mock_session)
    assert len(jobs) == 0


@pytest.mark.asyncio
async def test_create_job_invalid_name():
    mock_session = Mock()
    # Add async methods
    mock_session.commit = AsyncMock(side_effect=ValueError("Invalid name"))
    mock_session.refresh = AsyncMock()
    mock_session.rollback = AsyncMock()
    with pytest.raises(ValueError):
        await create_job(mock_session, "")


@pytest.mark.asyncio
async def test_add_event_invalid_payload():
    mock_session = Mock()
    # Add async methods
    mock_session.commit = AsyncMock(side_effect=ValueError("Invalid payload"))
    mock_session.refresh = AsyncMock()
    mock_session.rollback = AsyncMock()
    with pytest.raises(ValueError):
        await add_event(mock_session, "test", None)
