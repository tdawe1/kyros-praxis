from fastapi import FastAPI, WebSocket, Depends, HTTPException
from fastapi.websockets import WebSocketDisconnect
from jose import JWTError, jwt
from os import getenv
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from database import engine, get_db_session
from routers.jobs import router as jobs_router
from routers.events import router as events_router
from routers.tasks import router as tasks_router
from models import Base

SECRET_KEY = getenv("SECRET_KEY")  # Remove fallback for production readiness
ALGORITHM = "HS256"

app = FastAPI(title="Orchestrator API", version="0.1.0")


@app.get("/")
async def root():
  return {"message": "Orchestrator API is running"}

@app.get("/health")
async def health():
  return {"status": "healthy"}


@app.get("/healthz")
async def healthz(session: AsyncSession = Depends(get_db_session)):
  try:
    await session.execute("SELECT 1")
    return {"status": "ok"}
  except Exception:
    raise HTTPException(status_code=500, detail="Database unavailable")

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


# Routers
app.include_router(jobs_router)
app.include_router(events_router)
app.include_router(tasks_router)

if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=8000)
