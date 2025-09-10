from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect
from jose import JWTError, jwt
from os import getenv

SECRET_KEY = getenv("SECRET_KEY", "your-secret-key-change-in-prod")
ALGORITHM = "HS256"

app = FastAPI(title="Orchestrator API", version="0.1.0")

@app.get("/")
async def root():
  return {"message": "Orchestrator API is running"}

@app.get("/health")
async def health():
  return {"status": "healthy"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
  await websocket.accept()
  await websocket.send_json({"type": "connected", "message": "WebSocket connected"})

  try:
    while True:
      data = await websocket.receive_json()
      await websocket.send_json({"type": "echo", "payload": data})
  except WebSocketDisconnect:
    pass

if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=8000)
