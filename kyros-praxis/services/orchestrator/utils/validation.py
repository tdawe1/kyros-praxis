"""
Input Validation Utilities for Data Integrity

This module provides validation utilities for task and job creation inputs in the Kyros Orchestrator service.
It uses Pydantic models to define validation rules and ensure that input data meets the required criteria
before being processed by the system.

In the Kyros Orchestrator service, data validation is critical for:
- Ensuring data integrity across all task and job creation operations
- Preventing malformed or malicious data from entering the system
- Providing clear error messages to clients about invalid input
- Maintaining consistent data structures throughout the application

The validation includes:
- Required field validation
- String length and format validation
- Optional field handling
- Prevention of extra fields
- Error handling and reporting

MODELS:
1. BaseTaskJobCreate - Base model for task and job creation
2. TaskCreate - Task creation model (inherits from BaseTaskJobCreate)
3. JobCreate - Job creation model (inherits from BaseTaskJobCreate)

FUNCTIONS:
1. validate_task_input - Validate task creation input data
2. validate_job_input - Validate job creation input data
"""

from typing import Optional

from pydantic import BaseModel, ValidationError, constr


class BaseTaskJobCreate(BaseModel):
    """
    Base model for task and job creation.
    
    This model defines the common fields and validation rules for both tasks and jobs.
    It ensures that titles are non-empty and strips whitespace, and that descriptions
    are optional but properly handled. Extra fields are forbidden to prevent unexpected
    data from being processed.
    
    In the Kyros Orchestrator service, this base model ensures consistency between
    task and job creation inputs, enforcing the same validation rules for common fields.
    
    Attributes:
        title (str): Required title with minimum length of 1 character, whitespace stripped.
                    This field uses Pydantic's constr to enforce the minimum length and
                    strip whitespace automatically.
        description (Optional[str]): Optional description field. Can be None or any string.
        
    Example:
        >>> # Valid instance
        >>> base = BaseTaskJobCreate(title="  Sample Title  ", description="Sample description")
        >>> print(base.title)
        "Sample Title"
        >>> print(base.description)
        "Sample description"
        
        >>> # Title will be stripped of whitespace
        >>> base = BaseTaskJobCreate(title="  Title with spaces  ")
        >>> print(base.title)
        "Title with spaces"
    """
    title: constr(min_length=1, strip_whitespace=True)
    description: Optional[str] = None
    model_config = {"extra": "forbid"}


class TaskCreate(BaseTaskJobCreate):
    """
    Task creation model.
    
    This model inherits from BaseTaskJobCreate and is used specifically for validating
    task creation input data. It ensures that all required fields are present and valid
    before a task is created in the system.
    
    In the Kyros Orchestrator service, this model is used to validate all incoming
    task creation requests, ensuring data consistency and preventing invalid data
    from entering the system. It inherits all validation rules from BaseTaskJobCreate
    and can be extended with task-specific validation rules if needed.
    
    Example:
        >>> # Valid task creation
        >>> task = TaskCreate(title="Process user registration", description="Handle new user signups")
        >>> print(task.title)
        "Process user registration"
    """
    pass


class JobCreate(BaseTaskJobCreate):
    """
    Job creation model.
    
    This model inherits from BaseTaskJobCreate and is used specifically for validating
    job creation input data. It ensures that all required fields are present and valid
    before a job is created in the system.
    
    In the Kyros Orchestrator service, this model is used to validate all incoming
    job creation requests, ensuring data consistency and preventing invalid data
    from entering the system. It inherits all validation rules from BaseTaskJobCreate
    and can be extended with job-specific validation rules if needed.
    
    Example:
        >>> # Valid job creation
        >>> job = JobCreate(title="Generate monthly reports", description="Compile monthly analytics")
        >>> print(job.title)
        "Generate monthly reports"
    """
    pass


def validate_task_input(task_data: dict) -> TaskCreate:
    """
    Validate task creation input data.
    
    This function takes a dictionary of task creation data and validates it against
    the TaskCreate Pydantic model. It ensures that all required fields are present,
    properly formatted, and that no extra fields are included. If validation fails,
    it raises a ValueError with details about the validation errors.
    
    Args:
        task_data (dict): Dictionary containing task creation data
            Required keys:
                - title (str): Non-empty string with minimum length of 1 character
            Optional keys:
                - description (str, optional): Description of the task
        
    Returns:
        TaskCreate: Validated task creation model instance
        
    Raises:
        ValueError: If the input data fails validation with details about the errors
        
    Example:
        >>> # Valid input
        >>> task_data = {"title": "Process user registration", "description": "Handle new user signups"}
        >>> validated_task = validate_task_input(task_data)
        >>> print(validated_task.title)
        "Process user registration"
        
        >>> # Invalid input - missing title
        >>> invalid_data = {"description": "Handle new user signups"}
        >>> try:
        ...     validate_task_input(invalid_data)
        ... except ValueError as e:
        ...     print(e)
        ...
        "Invalid task input: ..."
    """
    try:
        return TaskCreate(**task_data)
    except ValidationError as e:
        raise ValueError(f"Invalid task input: {e}") from e


def validate_job_input(job_data: dict) -> JobCreate:
    """
    Validate job creation input data.
    
    This function takes a dictionary of job creation data and validates it against
    the JobCreate Pydantic model. It ensures that all required fields are present,
    properly formatted, and that no extra fields are included. If validation fails,
    it raises a ValueError with details about the validation errors.
    
    Args:
        job_data (dict): Dictionary containing job creation data
            Required keys:
                - title (str): Non-empty string with minimum length of 1 character
            Optional keys:
                - description (str, optional): Description of the job
        
    Returns:
        JobCreate: Validated job creation model instance
        
    Raises:
        ValueError: If the input data fails validation with details about the errors
        
    Example:
        >>> # Valid input
        >>> job_data = {"title": "Generate monthly reports", "description": "Compile monthly analytics"}
        >>> validated_job = validate_job_input(job_data)
        >>> print(validated_job.title)
        "Generate monthly reports"
        
        >>> # Invalid input - empty title
        >>> invalid_data = {"title": "", "description": "Compile monthly analytics"}
        >>> try:
        ...     validate_job_input(invalid_data)
        ... except ValueError as e:
        ...     print(e)
        ...
        "Invalid job input: ..."
    """
    try:
        return JobCreate(**job_data)
    except ValidationError as e:
        raise ValueError(f"Invalid job input: {e}") from e
