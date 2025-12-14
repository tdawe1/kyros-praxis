"""Enhanced error handling middleware."""

import logging
from typing import Union

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from ..core.config import settings


logger = logging.getLogger(__name__)


async def validation_exception_handler(
    request: Request, 
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    Handle Pydantic validation errors with detailed error messages.
    
    Args:
        request: FastAPI request
        exc: Validation error
        
    Returns:
        JSON response with validation error details
    """
    errors = []
    
    for error in exc.errors():
        field_path = " → ".join(str(x) for x in error["loc"] if x != "body")
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    logger.warning(f"Validation error on {request.url.path}: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "The request data failed validation",
            "details": errors
        }
    )


async def database_exception_handler(
    request: Request, 
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle database errors.
    
    Args:
        request: FastAPI request
        exc: Database error
        
    Returns:
        JSON response with error message
    """
    logger.error(f"Database error on {request.url.path}: {exc}", exc_info=True)
    
    # Check for integrity errors (unique constraints, etc.)
    if isinstance(exc, IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "Database Constraint Violation",
                "message": "The operation violates a database constraint (e.g., duplicate entry)",
                "details": str(exc.orig) if hasattr(exc, 'orig') else str(exc)
            }
        )
    
    # Generic database error
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database Error",
            "message": "An error occurred while accessing the database",
            "details": str(exc) if settings.DEBUG else None
        }
    )


async def generic_exception_handler(
    request: Request, 
    exc: Exception
) -> JSONResponse:
    """
    Handle all other unhandled exceptions.
    
    Args:
        request: FastAPI request
        exc: Unhandled exception
        
    Returns:
        JSON response with error message
    """
    logger.error(
        f"Unhandled exception on {request.url.path}: {exc}", 
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "details": str(exc) if settings.DEBUG else "Please contact support if this persists"
        }
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle HTTP exceptions with consistent format.
    
    Args:
        request: FastAPI request
        exc: HTTP exception
        
    Returns:
        JSON response with error details
    """
    from fastapi import HTTPException
    
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail if isinstance(exc.detail, str) else exc.detail.get("error", "Error"),
                "message": exc.detail if isinstance(exc.detail, str) else exc.detail.get("message", ""),
                "details": exc.detail if isinstance(exc.detail, dict) else None
            }
        )
    
    return await generic_exception_handler(request, exc)
