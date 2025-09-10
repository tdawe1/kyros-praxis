from pydantic import BaseModel
from typing import Optional

class BaseTaskJobCreate(BaseModel):
    title: str
    description: Optional[str] = None

class TaskCreate(BaseTaskJobCreate):
    pass

class JobCreate(BaseTaskJobCreate):
    pass

def validate_task_input(task_data: dict) -> TaskCreate:
    try:
        return TaskCreate(**task_data)
    except ValueError as e:
        raise ValueError(f"Invalid task input: {e}") from e

 def validate_job_input(job_data: dict) -> JobCreate:
     try:
         return JobCreate(**job_data)
     except ValidationError as e:
         raise ValueError(f"Invalid job input: {e}") from e