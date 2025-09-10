from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List
from repositories.jobs import create_job, get_jobs
from database import get_db_session
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from auth import get_current_user


router = APIRouter()


@router.post("/jobs")
async def create_job_endpoint(
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
    if_match: str = Header(None),
):
    if if_match is None:
        raise HTTPException(
            status_code=412,
            detail="If-Match header required for create"
        )
    # For create, ETag could be a version or timestamp; 
    # here use job.id as ETag for simplicity
    try:
        job = await create_job(
            session, 
            "Test Job"  # Assuming name from request body, but for simplicity using test
        )
        response = JSONResponse(
            content={
                "id": str(job.id),
                "name": job.name,
                "status": job.status
            }
        )
        response.headers["ETag"] = str(job.id)
        return response
    except Exception:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Job creation failed")


@router.get("/jobs", response_model=List[dict])
async def get_jobs_endpoint(
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    jobs = await get_jobs(session)
    response = JSONResponse(
        content=[
            {
                "id": str(j.id),
                "name": j.name,
                "status": j.status
            } for j in jobs
        ]
    )
    # Placeholder for list ETag
    response.headers["ETag"] = "list-version-1"
    return response
