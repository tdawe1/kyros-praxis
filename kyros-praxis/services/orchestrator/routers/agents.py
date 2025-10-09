"""
Agents API Router (stub)

Provides minimal endpoints for the Agents UI to avoid 404s during initial
frontend development. Endpoints return empty payloads and require auth for
consistency with secured routes.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

try:
    from ..database import get_db_session
    from ..models import User
    from ..auth import JWT_ISSUER, JWT_AUDIENCE, SECRET_KEY, ALGORITHM
except ImportError:  # pragma: no cover
    from services.orchestrator.database import get_db_session  # type: ignore
    from services.orchestrator.models import User  # type: ignore
    from services.orchestrator.auth import JWT_ISSUER, JWT_AUDIENCE, SECRET_KEY, ALGORITHM  # type: ignore

from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/agents", tags=["agents"])
oauth2_scheme = HTTPBearer(auto_error=False)


async def get_current_user_async(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),  # noqa: F401
):
    """Validate JWT and return a dummy user object for auth gatekeeping.

    This does not look up the user in DB to keep the stub minimal, but
    verifies the token structure to avoid accepting random strings.
    """
    from fastapi import status

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None or not getattr(credentials, "credentials", None):
        raise credentials_exception

    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Return a minimal user-like object
    return {"username": username}


class Agent(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str = Field("active", pattern="^(active|paused|error|pending)$")
    model: Optional[str] = None
    owner: Optional[str] = None
    capabilities: List[str] = []
    successRate: Optional[float] = None
    lastRunAt: Optional[datetime] = None


class AgentListResponse(BaseModel):
    agents: List[Agent]
    total: int
    page: int
    pageSize: int


@router.get("/", response_model=AgentListResponse, summary="List agents (stub)")
async def list_agents(
    page: int = 1,
    pageSize: int = 20,
    status: Optional[str] = None,  # noqa: F841
    sortBy: Optional[str] = None,  # noqa: F841
    sortOrder: Optional[str] = None,  # noqa: F841
    current_user: User = Depends(get_current_user_async),  # noqa: F841
):
    """Return an empty list with paging info for now."""
    return AgentListResponse(agents=[], total=0, page=page, pageSize=pageSize)

