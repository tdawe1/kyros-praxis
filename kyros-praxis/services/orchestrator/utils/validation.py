from pydantic import BaseModel, ValidationError
from typing import Optional


class BaseTaskJobCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: Optional[Annotated[str, Field(max_length=2000)]] = None


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