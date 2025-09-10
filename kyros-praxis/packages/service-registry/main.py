import os
import logging
import subprocess
from fastapi import FastAPI, Depends, HTTPException, status, Request, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
from datetime import datetime
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, String, DateTime, JSON, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis

Base = declarative_base()

class Service(Base):
    __tablename__ = "registered_services"
    name = Column(String, primary_key=True)
    host = Column(String)
    port = Column(String)
    capabilities = Column(JSON)
    last_heartbeat = Column(DateTime)

engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///services.db"))

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(title="Kyros Service Registry", version="1.0.0")

# CORS
ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic request id logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("service-registry")

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    req_id = request.headers.get("x-request-id") or os.urandom(8).hex()
    response = await call_next(request)
    response.headers["x-request-id"] = req_id
    logger.info(
        {
            "event": "http_request",
            "id": req_id,
            "path": request.url.path,
        }
    )
    return response

class ServiceRegistration(BaseModel):
    name: str
    host: str
    port: str
    capabilities: Dict[str, str]

class ServiceHealthCheck(BaseModel):
    name: str
    status: str
    timestamp: datetime

# Dependency Injection example (FastAPI Depends)

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return {"user_id": user_id}

@app.post("/register")
async def register_service(
    service: ServiceRegistration,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Register service
    service_instance = Service(
        name=service.name,
        host=service.host,
        port=service.port,
        capabilities=service.capabilities,
        last_heartbeat=datetime.utcnow(),
    )
    db.add(service_instance)
    db.commit()

    return {"status": "registered", "service": service.name}

@app.get("/services")
async def list_services(
    db=Depends(get_db), current_user: dict = Depends(get_current_user)
):
    services = db.query(Service).all()
    return {
        "services": [
            {
                "name": s.name,
                "host": s.host,
                "port": s.port,
                "capabilities": s.capabilities,
                "last_heartbeat": s.last_heartbeat,
            }
            for s in services
        ]
    }

@app.delete("/unregister/{service_name}")
async def unregister_service(
    service_name: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = db.query(Service).filter(Service.name == service_name).first()
    if service:
        db.delete(service)
        db.commit()
        return {"status": "unregistered", "service": service_name}
    raise HTTPException(status_code=404, detail="Service not found")

@app.get("/health/{service_name}")
async def health_check(
    service_name: str, db=Depends(get_db)
):
    service = db.query(Service).filter(Service.name == service_name).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Check if service is healthy (mock - ping in production)
    is_healthy = (
        service.last_heartbeat.timestamp()
        > (datetime.utcnow().timestamp() - 60)
    )  # 60s heartbeat timeout
    health = ServiceHealthCheck(
        name=service_name,
        status="healthy" if is_healthy else "unhealthy",
        timestamp=datetime.utcnow(),
    )
    return health

@app.get("/readyz")
async def readyz(db=Depends(get_db)):
    try:
        # Check DB
        db.execute(text("SELECT 1")).scalar()
        # Check Redis
        redis_url = os.getenv("REDIS_URL", "redis://kyros-praxis-redis:6379")
        r = redis.from_url(redis_url)
        r.ping()
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Not ready")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Extract token from subprotocol
    if not websocket.subprotocol:
        await websocket.close(code=1008, reason="No token provided")
        return

    token = websocket.subprotocol[0]  # Assuming single subprotocol token

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            await websocket.close(code=1008, reason="Invalid token")
            return
    except JWTError:
        await websocket.close(code=1008, reason="Invalid token")
        return

    await websocket.accept()
    await websocket.send_json({"type": "connected", "user_id": user_id})

    # Handle messages
    try:
        while True:
            data = await websocket.receive_json()
            # Echo back for test
            await websocket.send_json({"type": "echo", "payload": data})
    except Exception:
        pass

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)

@app.on_event("startup")
def startup():
    try:
        # Run Alembic migrations if available; do not crash service on failure
        subprocess.run(["alembic", "upgrade", "head"], cwd=".", check=False)
    except Exception:
        pass
