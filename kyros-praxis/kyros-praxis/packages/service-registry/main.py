from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
from datetime import datetime

app = FastAPI(title="Kyros Service Registry", version="1.0.0")

# In-memory storage for registered services (migrate to Postgres later)
registered_services: Dict[str, dict] = {}


class ServiceRegistration(BaseModel):
    name: str
    host: str
    port: int
    capabilities: list[str]


class ServiceHealthCheck(BaseModel):
    name: str
    status: str
    timestamp: datetime


@app.post("/register")
async def register_service(service: ServiceRegistration):
    # Register service
    registered_services[service.name] = {
        "name": service.name,
        "host": service.host,
        "port": service.port,
        "capabilities": service.capabilities,
        "last_heartbeat": datetime.utcnow()
    }
    return {"status": "registered", "service": service.name}


@app.delete("/unregister/{service_name}")
async def unregister_service(service_name: str):
    if service_name in registered_services:
        del registered_services[service_name]
        return {"status": "unregistered", "service": service_name}
    raise HTTPException(status_code=404, detail="Service not found")


@app.get("/health/{service_name}")
async def health_check(service_name: str):
    service = registered_services.get(service_name)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Check if service is healthy (mock - ping in production)
    is_healthy = (
        service["last_heartbeat"].timestamp()
        > (datetime.utcnow().timestamp() - 60)
    )  # 60s heartbeat timeout
    health = ServiceHealthCheck(
        name=service_name,
        status="healthy" if is_healthy else "unhealthy",
        timestamp=datetime.utcnow()
    )
    return health


@app.get("/services")
async def list_services():
    healthy_services = []
    for service in registered_services.values():
        is_healthy = (
            service["last_heartbeat"].timestamp()
            > (datetime.utcnow().timestamp() - 60)
        )
        healthy_service = {
            "name": service["name"],
            "host": service["host"],
            "port": service["port"],
            "capabilities": service["capabilities"],
            "status": "healthy" if is_healthy else "unhealthy"
        }
        healthy_services.append(healthy_service)
    return {"services": healthy_services}

@app.get("/discovery")
async def discovery():
    # Discovery endpoint for service lookup
    return {
        "services": registered_services,
        "timestamp": datetime.utcnow()
    }

@app.get("/lookup/{capability}")
async def lookup_by_capability(capability: str):
    matching_services = [
        s for s in registered_services.values()
        if capability in s["capabilities"]
    ]
    return {"services": matching_services, "capability": capability}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
