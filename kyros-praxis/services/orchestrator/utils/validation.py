from pydantic import BaseModel, ValidationError, constr
from typing import Optional


class BaseTaskJobCreate(BaseModel):
    title: constr(min_length=1, strip_whitespace=True)
    description: Optional[str] = None
    model_config = {"extra": "forbid"}


class TaskCreate(BaseTaskJobCreate):
    pass


class JobCreate(BaseTaskJobCreate):
    pass


def validate_task_input(task_data: dict) -> TaskCreate:
    try:
        return TaskCreate(**task_data)
    except ValidationError as e:
        raise ValueError(f"Invalid task input: {e}") from e


def validate_job_input(job_data: dict) -> JobCreate:
    try:
        return JobCreate(**job_data)
    except ValidationError as e:
        raise ValueError(f"Invalid job input: {e}") from e