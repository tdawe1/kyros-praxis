from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, EmailStr


class RunStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    canceled = "canceled"


class RunCreate(BaseModel):
    crew_id: str = Field(..., description="ID of the crew manifest to use")
    input: Dict[str, Any] = Field(default_factory=dict, description="Inputs for the crew run")


class Run(BaseModel):
    id: str
    crew_id: str
    status: RunStatus
    input: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None


class CancelRequest(BaseModel):
    reason: Optional[str] = None


# Authentication Models
class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserResponse(UserBase):
    id: str
    role: str
    active: bool
    created_at: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    email: Optional[str] = None

