"""
Collaborative Task Management API Router Module

This module provides RESTful API endpoints for managing collaborative tasks in the Kyros Orchestrator service.
It includes endpoints for creating, listing, retrieving, updating, and deleting tasks, with proper
authentication, authorization, and validation. Tasks represent collaborative work items that can be shared
and managed between different systems or users within the orchestrator ecosystem.

Collaborative tasks enable:
- Cross-system task coordination
- Shared work management
- Version-controlled task updates
- ETag-based caching for efficient data transfer
- Conditional request handling for reduced bandwidth

The router implements best practices for API design including:
- Synchronous database operations
- Proper error handling
- Authentication and authorization
- Input validation
- ETag-based caching
- Comprehensive logging
- Conditional requests

Task Management Features:
- Full CRUD operations for collaborative tasks
- Optimistic concurrency control with versioning
- ETag-based caching for improved performance
- Conditional GET requests to reduce bandwidth
- Comprehensive audit logging for all operations
- Input validation to ensure data integrity

ENDPOINTS:
1. POST /collab/tasks - Create a new collaborative task
2. GET /collab/state/tasks - List all collaborative tasks
3. GET /collab/tasks/{task_id} - Retrieve a specific task
4. PUT /collab/tasks/{task_id} - Update a specific task
5. DELETE /collab/tasks/{task_id} - Delete a task
"""

import hashlib
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.orm import Session

try:
    # When running as a package (e.g., tests in monorepo)
    from auth import User, get_current_user
    from database import get_db
    from models import Task
    from utils.validation import TaskCreate, validate_task_input
    from app.core.logging import log_orchestrator_event
except ImportError:
    # Fallback when running module directly
    from services.orchestrator.auth import User, get_current_user  # type: ignore
    from services.orchestrator.database import get_db  # type: ignore
    from services.orchestrator.models import Task  # type: ignore
    from services.orchestrator.utils.validation import TaskCreate, validate_task_input  # type: ignore
    from services.orchestrator.app.core.logging import log_orchestrator_event  # type: ignore

# Create the API router for task endpoints
router = APIRouter()


@router.post("/collab/tasks", summary="Create a new collaborative task", description="Create a new collaborative task with the specified parameters and return the created task details")
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    response: Response = None,
):
    """
    Create a new collaborative task.
    
    This endpoint creates a new collaborative task in the orchestrator system with the specified
    parameters. The task can be used for collaborative work between different systems or users.
    The endpoint performs input validation, creates the task in the database, and returns the
    task details with an ETag for caching purposes.
    
    Args:
        task (TaskCreate): Task creation parameters including title and description
        db (Session): Database session dependency
        current_user (User): Authenticated user (from get_current_user dependency)
        response (Response): FastAPI response object for setting headers and status codes
        
    Returns:
        dict: Created task details including ID, title, description, version, and creation timestamp
        
    Raises:
        HTTPException: If input validation fails or database operation encounters an error
    """
    validated_input = validate_task_input(task.model_dump())
    db_task = Task(**validated_input.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    task_dict = {
        "id": db_task.id,
        "title": db_task.title,
        "description": db_task.description,
        "version": db_task.version,
        "created_at": db_task.created_at.isoformat(),
    }
    
    # Log orchestrator event
    log_orchestrator_event(
        event="task_created",
        task_id=str(db_task.id),
        user_id=current_user.id,
        title=db_task.title,
        description=db_task.description
    )
    
    canonical = json.dumps(task_dict, sort_keys=True)
    etag = hashlib.sha256(canonical.encode()).hexdigest()
    if response is not None:
        response.status_code = 201
        response.headers["ETag"] = f'"{etag}"'
        response.headers["Location"] = f"/collab/tasks/{task_dict['id']}"
    return task_dict


@router.get("/collab/state/tasks", summary="List all collaborative tasks", description="List all collaborative tasks with support for conditional requests and ETag-based caching")
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    response: Response = None,
    if_none_match: Optional[str] = Header(default=None, alias="If-None-Match"),
):
    """
    List all collaborative tasks.
    
    This endpoint retrieves a list of all collaborative tasks from the orchestrator system.
    It implements ETag-based caching to reduce bandwidth usage and improve performance for
    clients that poll this endpoint frequently. The endpoint supports conditional GET requests
    using the If-None-Match header.
    
    Args:
        db (Session): Database session dependency
        current_user (User): Authenticated user (from get_current_user dependency)
        response (Response): FastAPI response object for setting headers and status codes
        if_none_match (Optional[str]): Client's ETag for conditional requests (If-None-Match header)
        
    Returns:
        dict: Dictionary containing task list with "kind" and "items" keys
        
    Raises:
        HTTPException: If database operation encounters an error
    """
    tasks = db.query(Task).all()
    items = []
    for t in tasks:
        items.append(
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "version": t.version,
                "created_at": t.created_at.isoformat(),
            }
        )
    
    # Log orchestrator event
    log_orchestrator_event(
        event="tasks_listed",
        user_id=current_user.id,
        count=len(items)
    )
    
    canonical = json.dumps(items, sort_keys=True)
    etag = hashlib.sha256(canonical.encode()).hexdigest()

    quoted = f'"{etag}"'
    # Conditional GET support
    if if_none_match:
        # handle multiple ETags in header, quoted or unquoted
        candidates = [v.strip() for v in if_none_match.split(",")]
        if etag in candidates or quoted in candidates:
            return Response(status_code=304)

    if response is not None:
        response.headers["ETag"] = quoted
    return {"kind": "tasks", "items": items}


@router.get("/collab/tasks/{task_id}", summary="Get a specific task by ID", description="Retrieve a specific collaborative task by its unique identifier with ETag-based caching support")
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    response: Response = None,
    if_none_match: Optional[str] = Header(default=None, alias="If-None-Match"),
):
    """
    Get a specific task by ID.
    
    This endpoint retrieves the details of a specific collaborative task identified by its
    unique ID. If the task does not exist, it returns a 404 Not Found error. The endpoint
    implements ETag-based caching to reduce bandwidth usage and improve performance for
    clients that poll this endpoint frequently. It supports conditional GET requests
    using the If-None-Match header.
    
    Args:
        task_id (int): ID of the task to retrieve
        db (Session): Database session dependency
        current_user (User): Authenticated user (from get_current_user dependency)
        response (Response): FastAPI response object for setting headers and status codes
        if_none_match (Optional[str]): Client's ETag for conditional requests (If-None-Match header)
        
    Returns:
        dict: Task details including ID, title, description, version, and creation timestamp
        
    Raises:
        HTTPException: If the task is not found (status code 404)
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        # Log orchestrator event
        log_orchestrator_event(
            event="task_not_found",
            task_id=str(task_id),
            user_id=current_user.id
        )
        
        return Response(status_code=404, content="Task not found")
    
    task_dict = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "version": task.version,
        "created_at": task.created_at.isoformat(),
    }
    
    # Log orchestrator event
    log_orchestrator_event(
        event="task_retrieved",
        task_id=str(task.id),
        user_id=current_user.id,
        title=task.title
    )
    
    canonical = json.dumps(task_dict, sort_keys=True)
    etag = hashlib.sha256(canonical.encode()).hexdigest()

    quoted = f'"{etag}"'
    # Conditional GET support
    if if_none_match:
        # handle multiple ETags in header, quoted or unquoted
        candidates = [v.strip() for v in if_none_match.split(",")]
        if etag in candidates or quoted in candidates:
            return Response(status_code=304)

    if response is not None:
        response.headers["ETag"] = quoted
    return task_dict


@router.put("/collab/tasks/{task_id}", summary="Update a specific task by ID", description="Update a specific collaborative task by its unique identifier and return the updated task details")
def update_task(
    task_id: int,
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    response: Response = None,
):
    """
    Update a specific task by ID.
    
    This endpoint updates a specific collaborative task identified by its unique ID with new
    data. It increments the task version to support optimistic concurrency control. If the task
    does not exist, it returns a 404 Not Found error. The endpoint performs input validation,
    updates the task in the database, and returns the updated task details with an ETag for
    caching purposes.
    
    Args:
        task_id (int): ID of the task to update
        task (TaskCreate): Updated task data including title and description
        db (Session): Database session dependency
        current_user (User): Authenticated user (from get_current_user dependency)
        response (Response): FastAPI response object for setting headers
        
    Returns:
        dict: Updated task details including ID, title, description, version, and creation timestamp
        
    Raises:
        HTTPException: If the task is not found (status code 404)
    """
    db_task = db.query(Task).filter(Task.id == task_id).first()
    
    if not db_task:
        # Log orchestrator event
        log_orchestrator_event(
            event="task_not_found_for_update",
            task_id=str(task_id),
            user_id=current_user.id
        )
        
        return Response(status_code=404, content="Task not found")
    
    # Store old values for logging
    old_title = db_task.title
    old_description = db_task.description
    
    # Update task
    validated_input = validate_task_input(task.model_dump())
    db_task.title = validated_input.title
    db_task.description = validated_input.description
    db_task.version += 1
    db.commit()
    db.refresh(db_task)
    
    task_dict = {
        "id": db_task.id,
        "title": db_task.title,
        "description": db_task.description,
        "version": db_task.version,
        "created_at": db_task.created_at.isoformat(),
    }
    
    # Log orchestrator event
    log_orchestrator_event(
        event="task_updated",
        task_id=str(db_task.id),
        user_id=current_user.id,
        old_title=old_title,
        new_title=db_task.title,
        old_description=old_description,
        new_description=db_task.description
    )
    
    canonical = json.dumps(task_dict, sort_keys=True)
    etag = hashlib.sha256(canonical.encode()).hexdigest()
    if response is not None:
        response.headers["ETag"] = f'"{etag}"'
    return task_dict


@router.delete("/collab/tasks/{task_id}", summary="Delete a specific task by ID", description="Delete a specific collaborative task by its unique identifier")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    response: Response = None,
):
    """
    Delete a specific task by ID.
    
    This endpoint deletes a specific collaborative task identified by its unique ID.
    It's typically used for cleanup operations or when tasks are no longer needed.
    If the task does not exist, it returns a 404 Not Found error. The endpoint logs
    both successful deletions and not-found attempts for audit and monitoring purposes.
    
    Args:
        task_id (int): ID of the task to delete
        db (Session): Database session dependency
        current_user (User): Authenticated user (from get_current_user dependency)
        response (Response): FastAPI response object for setting status codes
        
    Returns:
        dict: Success confirmation message
        
    Raises:
        HTTPException: If the task is not found (status code 404)
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        # Log orchestrator event
        log_orchestrator_event(
            event="task_not_found_for_deletion",
            task_id=str(task_id),
            user_id=current_user.id
        )
        
        return Response(status_code=404, content="Task not found")
    
    # Store task title for logging before deletion
    task_title = task.title
    
    # Delete task
    db.delete(task)
    db.commit()
    
    # Log orchestrator event
    log_orchestrator_event(
        event="task_deleted",
        task_id=str(task_id),
        user_id=current_user.id,
        title=task_title
    )
    
    if response is not None:
        response.status_code = 204
    return {"message": "Task deleted successfully"}