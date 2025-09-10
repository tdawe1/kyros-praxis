from fastapi import FastAPI, WebSocket, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocketDisconnect
from jose import jwt  # used for token encoding in auth module
from os import getenv
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: F401 (placeholder for future async endpoints)
from sqlalchemy.orm import Session
from datetime import timedelta

from .database import engine, get_db
from sqlalchemy import text
from .routers.jobs import router as jobs_router
from .routers.tasks import router as tasks_router
# asyncio only needed for websocket echo; keep optional
from .models import Base

from .auth import create_access_token, Token, authenticate_user, Login

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    HAVE_SLOWAPI = True
except Exception:  # pragma: no cover - optional dependency in local runs
    Limiter = None  # type: ignore
    SlowAPIMiddleware = None  # type: ignore
    RateLimitExceeded = Exception  # type: ignore
    HAVE_SLOWAPI = False
from .middleware import api_key_validator, limiter_key_func

SECRET_KEY = getenv("SECRET_KEY")  # Remove fallback for production readiness
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


app = FastAPI(title="Orchestrator API", version="0.1.0")

REDIS_URL = getenv("REDIS_URL", "memory://")
if HAVE_SLOWAPI:
    app.state.limiter = Limiter(
        key_func=limiter_key_func,
        storage_uri=REDIS_URL,
        default_limits=["60/minute"],
    )
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)  


@app.get("/")
async def root():
    return {"message": "Orchestrator API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/healthz")
def healthz(db = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=500, detail="Database unavailable")


@app.post("/auth/login", response_model=Token)
def login_for_access_token(
    login: Login,
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, login.email, login.password)
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


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json({"type": "connected", "message": "WebSocket connected"})

    try:
        while True:
            data: dict[str, Any] = await websocket.receive_json()
            await websocket.send_json({"type": "echo", "payload": data})
    except WebSocketDisconnect:
        await websocket.close(code=1000)

# Expose handler for tests that introspect attribute existence
app.websocket_endpoint = websocket_endpoint


# Exception handlers
@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def http_exception_handler_401(request, exc):
    return JSONResponse({"type": "unauthorized", "message": "Could not validate credentials"}, status_code=401)


@app.exception_handler(status.HTTP_403_FORBIDDEN)
async def http_exception_handler_403(request, exc):
    return JSONResponse({"type": "forbidden", "message": "Not enough permissions to access resource"}, status_code=403)


@app.exception_handler(status.HTTP_404_NOT_FOUND)
async def http_exception_handler_404(request, exc):
    return JSONResponse({"type": "not_found", "message": "Resource not found"}, status_code=404)


@app.exception_handler(status.HTTP_422_UNPROCESSABLE_ENTITY)
async def http_exception_handler_422(request, exc):
    return JSONResponse({"type": "unprocessable_entity", "message": "Validation error", "details": exc.detail}, status_code=422)


# Routers
app.include_router(jobs_router, dependencies=[Depends(api_key_validator)])
app.include_router(tasks_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
