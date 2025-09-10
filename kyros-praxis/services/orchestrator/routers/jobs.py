from fastapi import APIRouter, HTTPException, Depends

from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from ..auth import get_current_user, User

# (No direct Job import needed at import-time)

async def get_db_session():
    # Lazy import to avoid loading async drivers during unrelated tests
    from ..repositories.database import get_db_session as _inner
    async for s in _inner():
        yield s


router = APIRouter()

@router.post("/jobs")
async def create_job_endpoint(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    try:
        from ..repositories.jobs import create_job as _create_job
        job = await _create_job(session, "Test Job")
        response = JSONResponse(
            content={
                "job_id": str(job.id),
                "status": "accepted",
            }
        )
        response.headers["ETag"] = str(job.id)
        return response
    except Exception:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Job creation failed")


@router.get("/jobs")
async def get_jobs_endpoint(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    from ..repositories.jobs import get_jobs as _get_jobs
    jobs = await _get_jobs(session)
    response = JSONResponse(
        content={
            "jobs": [
                {"id": str(j.id), "name": j.name, "status": j.status}
                for j in jobs
            ]
        }
    )
    response.headers["ETag"] = "list-version-1"
    return response
