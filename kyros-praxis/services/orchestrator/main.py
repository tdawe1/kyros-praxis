from datetime import timedelta

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    WebSocket,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,  # noqa: F401 (placeholder for future async endpoints)
)

from .auth import (
    User,
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user,
    Login,
)
from .database import get_db
from sqlalchemy import text
from .routers import jobs, tasks

app = FastAPI(title="Orchestrator API", version="0.1.0")

app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(tasks.router, prefix="/collab", tags=["collab"])


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
async def login(payload: Login, db=Depends(get_db)) -> dict:
    """Login endpoint."""
    user = authenticate_user(db, payload.email, payload.password)
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
