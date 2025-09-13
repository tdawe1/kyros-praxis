from datetime import timedelta
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    WebSocket,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,  # noqa: F401 (placeholder for future async endpoints)
)

try:
    # When running as a package (e.g., tests in monorepo)
    from .auth import (
        User,
        authenticate_user,
        create_access_token,
        ACCESS_TOKEN_EXPIRE_MINUTES,
        get_current_user,
    )
    from .database import get_db
    from .routers import jobs, tasks, utils
    from .app.core.config import settings
except Exception:  # Fallback when running module directly in container (/app)
    from auth import (  # type: ignore
        User,
        authenticate_user,
        create_access_token,
        ACCESS_TOKEN_EXPIRE_MINUTES,
        get_current_user,
    )
    from database import get_db  # type: ignore
    import routers.jobs as jobs  # type: ignore
    import routers.tasks as tasks  # type: ignore
    import routers.utils as utils  # type: ignore
    from app.core.config import settings  # type: ignore

app = FastAPI(
    title=settings.PROJECT_NAME + " - Orchestrator API",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# API v1 routers
API_V1_STR = settings.API_V1_STR
app.include_router(jobs.router, prefix=f"{API_V1_STR}/jobs", tags=["jobs"])
app.include_router(tasks.router, prefix=f"{API_V1_STR}/collab", tags=["collab"])
app.include_router(utils.router, prefix=f"{API_V1_STR}/utils", tags=["utils"])


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {"message": "Orchestrator API is running"}


@app.get("/health")
async def health() -> dict:
    """Health check."""
    return {"status": "healthy"}


@app.get("/healthz")
def healthz(db=Depends(get_db)) -> dict:
    """Health check with DB ping."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=500, detail="DB unavailable")


@app.post("/auth/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)
) -> dict:
    """Login endpoint."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, current_user: User = Depends(get_current_user)
) -> None:
    """WebSocket endpoint with authentication."""
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        await websocket.send_json({"data": data})
