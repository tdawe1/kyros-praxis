from fastapi import FastAPI, WebSocket, Depends, HTTPException, status, Body
from fastapi.websockets import WebSocketDisconnect
from jose import JWTError, jwt
from os import getenv
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from datetime import timedelta

from database import engine, get_db
from routers.jobs import router as jobs_router
from routers.events import router as events_router
from routers.tasks import router as tasks_router
import asyncio
from models import Base

from auth import create_access_token, Token, authenticate_user, oauth2_scheme, Login

SECRET_KEY = getenv("SECRET_KEY")  # Remove fallback for production readiness
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


app = FastAPI(title="Orchestrator API", version="0.1.0")


@app.get("/")
async def root():
    return {"message": "Orchestrator API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/healthz")
def healthz(db = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=500, detail="Database unavailable")


@app.post("/auth/login", response_model=Token)
def login_for_access_token(
    login: Login = Body(...),
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
    return {"type": "unauthorized", "message": "Could not validate credentials"}


@app.exception_handler(status.HTTP_403_FORBIDDEN)
async def http_exception_handler_403(request, exc):
    return {"type": "forbidden", "message": "Not enough permissions to access resource"}


@app.exception_handler(status.HTTP_404_NOT_FOUND)
async def http_exception_handler_404(request, exc):
    return {"type": "not_found", "message": "Resource not found"}


@app.exception_handler(status.HTTP_422_UNPROCESSABLE_ENTITY)
async def http_exception_handler_422(request, exc):
    return {"type": "unprocessable_entity", "message": "Validation error", "details": exc.detail}


# Routers
app.include_router(jobs_router)
app.include_router(events_router)
app.include_router(tasks_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
