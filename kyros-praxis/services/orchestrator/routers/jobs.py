"""
Job Management API Router Module

This module provides RESTful API endpoints for managing jobs in the Kyros Orchestrator service.
It includes endpoints for creating, listing, retrieving, updating, and deleting jobs, with
proper authentication, authorization, and validation. Jobs represent units of work that can
be processed by various workers in the system.

The router implements best practices for API design including:
- Asynchronous database operations
- Proper error handling
- Authentication and authorization
- Input validation
- ETag-based caching
- Comprehensive logging
- Conditional requests

Job Lifecycle:
1. Created (pending) - Job is created and waiting to be processed
2. Running - Job is currently being processed by a worker
3. Completed - Job has finished successfully
4. Failed - Job encountered an error during processing
5. Cancelled - Job was manually cancelled

Key Features:
- Full CRUD operations for job management
- Status updates to track job progress
- Pagination support for listing jobs
- Conditional requests with ETag caching
- Comprehensive error handling and logging
- Authentication and authorization for all operations

ENDPOINTS:
1. POST /jobs - Create a new job
2. GET /jobs - List jobs with optional filtering
3. GET /jobs/{job_id} - Retrieve a specific job
4. PUT /jobs/{job_id}/status - Update job status
5. DELETE /jobs/{job_id} - Delete a job
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

# When running as a package
from ..database import get_db_session
from ..models import Job, User
from ..utils.validation import JobCreate, validate_job_input
from ..utils import generate_etag
from ..app.core.logging import log_orchestrator_event

from jose import jwt

# Create the API router for job endpoints
router = APIRouter()

# HTTP Bearer authentication scheme for JWT tokens
oauth2_scheme = HTTPBearer(auto_error=False)


# Async authentication functions
async def get_user_async(session: AsyncSession, username: str) -> Optional[User]:
    """
    Retrieve a user from the database asynchronously by username.
    
    Performs an asynchronous database query to find a user with the specified username.
    
    Args:
        session (AsyncSession): Asynchronous database session
        username (str): Username to search for
        
    Returns:
        Optional[User]: User object if found, None otherwise
    """
    from sqlalchemy import select
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_current_user_async(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
):
    """
    FastAPI dependency to get the current authenticated user from JWT token asynchronously.
    
    Decodes the JWT token from the Authorization header, validates it, and
    retrieves the corresponding user from the database using asynchronous operations.
    
    Args:
        credentials (HTTPAuthorizationCredentials): Bearer token from Authorization header
        session (AsyncSession): Asynchronous database session dependency
        
    Returns:
        User: Authenticated user object
        
    Raises:
        HTTPException: If token is missing, invalid, or user not found (401 Unauthorized)
    """
    from ..auth import JWT_ISSUER, JWT_AUDIENCE, SECRET_KEY, ALGORITHM
    from fastapi import HTTPException, status
    from jose import JWTError

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Check if credentials are provided
        if credentials is None or not getattr(credentials, "credentials", None):
            raise credentials_exception
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user_async(session, username)
    if user is None:
        raise credentials_exception
    return user


async def _create_job(session: AsyncSession, title: str):
    """
    Create a new job in the database asynchronously.
    
    Creates a new job with the specified title, commits it to the database,
    refreshes the instance to get the generated ID, and logs the creation event.
    
    Args:
        session (AsyncSession): Asynchronous database session
        title (str): Title for the new job
        
    Returns:
        Job: The created job object
    """
    # Map Day-1 JobCreate.title -> Job.name
    job = Job(name=title)
    session.add(job)
    await session.commit()
    await session.refresh(job)
    
    # Log orchestrator event
    log_orchestrator_event(
        event="job_created",
        task_id=str(job.id),
        title=job.name,
        status="created",
        timestamp=datetime.utcnow().isoformat()
    )
    
    return job


class JobStatus(str, Enum):
    """
    Enumeration of possible job statuses.
    
    Represents the lifecycle states of a job in the orchestrator system.
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobCreate(BaseModel):
    """
    Data model for creating a new job.
    
    This model defines the required parameters for creating a new job
    in the orchestrator system. The title should be a brief descriptive
    name that clearly indicates the purpose of the job.
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Brief descriptive name for the job",
        examples=["Analyze user feedback data"],
    )


class JobResponse(BaseModel):
    """
    Response model for job operations.
    
    This model defines the structure of job data returned by the API endpoints.
    It includes the job's unique identifier, name, status, and timestamps.
    """

    id: str
    name: str
    status: JobStatus = JobStatus.PENDING
    created_at: datetime
    updated_at: Optional[datetime] = None


@router.post("/jobs", response_model=JobResponse, status_code=201, summary="Create a new job", description="Create a new job with the specified parameters and return the created job details")
async def create_job(
    job: JobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user_async),
    response: Response = None,
):
    """
    Create a new job.
    
    This endpoint creates a new job in the orchestrator system with the specified
    parameters. The job is initially in 'pending' status and can be processed
    by the appropriate workers. The endpoint performs input validation,
    creates the job in the database, and returns the job details with an ETag
    for caching purposes.
    
    Args:
        job (JobCreate): Job creation parameters including title
            - title (str): Brief descriptive name for the job (1-255 characters)
        background_tasks (BackgroundTasks): FastAPI background tasks for async processing
        db (AsyncSession): Asynchronous database session dependency
        current_user (User): Authenticated user (from get_current_user_async dependency)
        response (Response): HTTP response object for setting headers
        
    Returns:
        JobResponse: Created job details including ID, name, status, and timestamps
            - id (str): Unique identifier for the job (UUID)
            - name (str): Name/title of the job
            - status (JobStatus): Current status of the job (pending, running, completed, failed, cancelled)
            - created_at (datetime): Timestamp when the job was created
            - updated_at (Optional[datetime]): Timestamp when the job was last updated
            
    Raises:
        HTTPException: If input validation fails or database operation encounters an error
            - 400: Invalid input parameters
            - 401: Authentication failed
            - 500: Internal server error during job creation
    """
    # Validate input
    validated_input = validate_job_input(job.model_dump())
    
    # Create job
    db_job = await _create_job(db, validated_input.title)
    
    # Log orchestrator event
    log_orchestrator_event(
        event="job_submitted",
        task_id=str(db_job.id),
        user_id=current_user.id,
        title=db_job.name,
        status="pending"
    )
    
    job_response = JobResponse(
        id=db_job.id,
        name=db_job.name,
        status=JobStatus.PENDING,
        created_at=db_job.created_at,
    )

    # Generate ETag for the response
    etag = generate_etag(job_response.model_dump())
    response.headers["ETag"] = etag

    return job_response


@router.get("/jobs", response_model=List[JobResponse], summary="List jobs", description="List jobs with optional filtering by status and pagination support")
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    status: Optional[JobStatus] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user_async),
    response: Response = None,
    if_none_match: Optional[str] = Header(default=None, alias="If-None-Match"),
):
    """
    List jobs with optional filtering by status.
    
    This endpoint retrieves a list of jobs from the orchestrator system with
    support for pagination and optional filtering by job status. It implements
    ETag-based caching to reduce bandwidth usage and improve performance for
    clients that poll this endpoint frequently.
    
    Args:
        skip (int): Number of jobs to skip for pagination (default: 0)
        limit (int): Maximum number of jobs to return (default: 100, max: 1000)
        status (Optional[JobStatus]): Filter jobs by status (pending, running, completed, etc.)
        db (AsyncSession): Asynchronous database session dependency
        current_user (User): Authenticated user (from get_current_user_async dependency)
        response (Response): HTTP response object for setting headers
        if_none_match (Optional[str]): Client's ETag for conditional requests (If-None-Match header)
        
    Returns:
        List[JobResponse]: List of job details matching the query criteria
            - id (str): Unique identifier for the job (UUID)
            - name (str): Name/title of the job
            - status (JobStatus): Current status of the job (pending, running, completed, failed, cancelled)
            - created_at (datetime): Timestamp when the job was created
            - updated_at (Optional[datetime]): Timestamp when the job was last updated
            
    Raises:
        HTTPException: If database operation encounters an error
            - 401: Authentication failed
            - 500: Internal server error during job listing
    """
    query = select(Job)
    if status:
        query = query.where(Job.status == status)
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    # Log orchestrator event
    log_orchestrator_event(
        event="jobs_listed",
        user_id=current_user.id,
        count=len(jobs),
        filter_status=status.value if status else None
    )
    
    job_responses = [
        JobResponse(
            id=job.id,
            name=job.name,
            status=JobStatus(job.status),
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
        for job in jobs
    ]

    # Generate ETag for the response
    response_data = [job.model_dump() for job in job_responses]
    etag = generate_etag(response_data)

    # Handle conditional requests
    if if_none_match:
        # Remove quotes from ETag for comparison
        client_etag = if_none_match.strip('"')
        server_etag = etag.strip('"')
        if client_etag == server_etag:
            response.status_code = 304
            return []

    # Set ETag header
    response.headers["ETag"] = etag

    return job_responses


@router.get("/jobs/{job_id}", response_model=JobResponse, summary="Get job by ID", description="Retrieve a specific job by its unique identifier")
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user_async),
):
    """
    Get a specific job by ID.
    
    This endpoint retrieves the details of a specific job identified by its
    unique ID. If the job does not exist, it returns a 404 Not Found error.
    The endpoint logs both successful retrievals and not-found attempts for
    audit and monitoring purposes.
    
    Args:
        job_id (str): ID of the job to retrieve
        db (AsyncSession): Asynchronous database session dependency
        current_user (User): Authenticated user (from get_current_user_async dependency)
        
    Returns:
        JobResponse: Job details including ID, name, status, and timestamps
        
    Raises:
        HTTPException: If the job is not found (status code 404)
    """
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        # Log orchestrator event
        log_orchestrator_event(
            event="job_not_found",
            task_id=str(job_id),
            user_id=current_user.id
        )
        
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Log orchestrator event
    log_orchestrator_event(
        event="job_retrieved",
        task_id=str(job.id),
        user_id=current_user.id,
        title=job.name,
        status=job.status
    )
    
    return JobResponse(
        id=job.id,
        name=job.name,
        status=JobStatus(job.status),
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.put("/jobs/{job_id}/status", response_model=JobResponse, summary="Update job status", description="Update the status of a specific job by its unique identifier")
async def update_job_status(
    job_id: str,
    status: JobStatus,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user_async),
):
    """
    Update the status of a job.
    
    This endpoint updates the status of a specific job identified by its unique ID.
    It's typically used by workers or administrators to update job progress or
    completion status. The endpoint logs both successful updates and not-found
    attempts for audit and monitoring purposes.
    
    Args:
        job_id (str): ID of the job to update
        status (JobStatus): New status for the job (pending, running, completed, failed, cancelled)
        db (AsyncSession): Asynchronous database session dependency
        current_user (User): Authenticated user (from get_current_user_async dependency)
        
    Returns:
        JobResponse: Updated job details including new status and updated timestamp
        
    Raises:
        HTTPException: If the job is not found (status code 404)
    """
    # Get the job
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        # Log orchestrator event
        log_orchestrator_event(
            event="job_not_found_for_status_update",
            task_id=str(job_id),
            user_id=current_user.id,
            new_status=status.value
        )
        
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Update the job status
    job.status = status.value
    job.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(job)
    
    # Log orchestrator event
    log_orchestrator_event(
        event="job_status_updated",
        task_id=str(job.id),
        user_id=current_user.id,
        title=job.name,
        old_status=job.status,  # This will be the old status
        new_status=status.value
    )
    
    return JobResponse(
        id=job.id,
        name=job.name,
        status=status,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.delete("/jobs/{job_id}", summary="Delete a job", description="Delete a specific job by its unique identifier")
async def delete_job(
    job_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user_async),
):
    """
    Delete a job.
    
    This endpoint deletes a specific job identified by its unique ID. It's typically
    used for cleanup operations or when jobs are no longer needed. The endpoint
    logs both successful deletions and not-found attempts for audit and monitoring
    purposes.
    
    Args:
        job_id (str): ID of the job to delete
        db (AsyncSession): Asynchronous database session dependency
        current_user (User): Authenticated user (from get_current_user_async dependency)
        
    Returns:
        dict: Success confirmation message
        
    Raises:
        HTTPException: If the job is not found (status code 404)
    """
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        # Log orchestrator event
        log_orchestrator_event(
            event="job_not_found_for_deletion",
            task_id=str(job_id),
            user_id=current_user.id
        )
        
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Store job name for logging before deletion
    job_name = job.name
    
    # Delete the job
    await db.execute(delete(Job).where(Job.id == job_id))
    await db.commit()
    
    # Log orchestrator event
    log_orchestrator_event(
        event="job_deleted",
        task_id=str(job_id),
        user_id=current_user.id,
        title=job_name
    )
    
    return {"message": "Job deleted successfully"}