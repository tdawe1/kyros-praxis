"""Main FastAPI application for the Orchestrator service.

This module defines the FastAPI application with authentication, job management,
and WebSocket endpoints for the Kyros platform.
"""

from datetime import timedelta

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    WebSocket,
    status,
)
from jose import jwt
from sqlalchemy.ext.asyncio import (
    AsyncSession,  # noqa: F401 (placeholder for future async endpoints)
)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

import auth
from auth import (
    User,
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user,
    Login,
    SECRET_KEY,
    ALGORITHM,
    get_user,
)
import database
from database import get_db
from sqlalchemy import text
import routers.jobs as jobs
import routers.tasks as tasks

app = FastAPI(title="Orchestrator API", version="0.1.0")

app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(tasks.router, prefix="/collab", tags=["collab"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)


@app.get("/")
async def root() -> dict:
    """Root endpoint returning API status message.

    Returns:
        Dictionary with status message
    """
    return {"message": "Orchestrator API is running"}


@app.get("/health")
async def health() -> dict:
    """Basic health check endpoint.

    Returns:
        Dictionary with health status
    """
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
async def login(payload: Login, db=Depends(get_db)) -> dict:
    """Authenticate user and return JWT access token.

    Args:
        payload: Login credentials (email, password)
        db: Database session dependency

    Returns:
        Dictionary containing access token and token type

    Raises:
        HTTPException: If authentication fails
    """
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, token: str = None
) -> None:
    """WebSocket endpoint with JWT authentication.

    Establishes a WebSocket connection after validating JWT token
    from query parameters. Echoes back received JSON messages.

    Args:
        websocket: WebSocket connection object
        token: JWT token from query parameters

    WebSocket Close Codes:
        4000: Missing token
        4001: Invalid token or user not found
    """
    # Verify JWT token from query parameters
    if not token:
        await websocket.close(code=4000)
        return

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience="api",
            issuer="https://orchestrator.local",
        )
        email: str = payload.get("sub")
        if email is None:
            await websocket.close(code=4001)
            return

        # Get user from database
        db = next(get_db())
        user = get_user(db, email=email)
        if user is None:
            await websocket.close(code=4001)
            return

    except jwt.JWTError:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        await websocket.send_json({"data": data})
