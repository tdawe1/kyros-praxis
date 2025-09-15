# Kyros Service Registry

The Kyros Service Registry is a centralized service discovery and registration system for the Kyros Praxis platform. It enables dynamic service registration, health monitoring, and discovery capabilities across the microservices architecture.

## 🏗️ Architecture

### Technology Stack
- **FastAPI** with Python 3.11+
- **Service Discovery Pattern**: Registration-based discovery
- **Health Monitoring**: Active and passive health checks
- **JWT Authentication**: Secure service-to-service communication
- **Caching**: Optional Redis caching for performance
- **Distributed Storage**: Future etcd integration for high availability

### Core Responsibilities
- **Service Registration**: Dynamic service endpoint registration
- **Service Discovery**: Query available services by type and capability
- **Health Monitoring**: Track service health and availability
- **Load Balancing**: Provide multiple endpoints for service types
- **Metadata Management**: Store service capabilities and configurations

## 🚀 Development Setup

### Prerequisites
- Python 3.11 or higher
- pip package manager
- Optional: Redis for caching
- Optional: etcd for distributed storage (future)

### Installation

1. **Navigate to package directory**:
   ```bash
   cd packages/service-registry
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**:
   ```bash
   cp .env.example .env
   ```

4. **Configure environment variables**:
   ```bash
   # Required
   SECRET_KEY=your_very_secure_secret_minimum_32_chars
   PORT=8001
   
   # Optional
   REDIS_URL=redis://localhost:6379
   ETCD_HOST=localhost:2379
   HEALTH_CHECK_INTERVAL=30
   SERVICE_EXPIRATION=300
   ```

### Running the Service

**Development Mode**:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

**Production Mode**:
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 2
```

### Testing API Connectivity

1. **Health Check**:
   ```bash
   curl http://localhost:8001/health
   ```

2. **Register Service**:
   ```bash
   curl -X POST http://localhost:8001/register \
     -H "Authorization: Bearer JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "id": "orchestrator-v1",
       "name": "orchestrator",
       "endpoint": "http://localhost:8000",
       "version": "1.0.0",
       "capabilities": ["job-orchestration", "ai-coordination"],
       "health_check": "http://localhost:8000/healthz"
     }'
   ```

3. **List Services**:
   ```bash
   curl -X GET http://localhost:8001/services \
     -H "Authorization: Bearer JWT_TOKEN"
   ```

## 📁 Project Structure

```
packages/service-registry/
├── main.py              # FastAPI application entry point
├── models.py            # Service registration models
├── database.py          # Storage abstraction layer
├── storage/
│   ├── memory.py        # In-memory storage implementation
│   └── redis.py         # Redis storage implementation (future)
├── health/
│   ├── checker.py       # Health check implementation
│   └── monitor.py       # Health monitoring service
├── auth.py             # Authentication and authorization
├── utils/
│   └── validation.py   # Input validation
└── tests/              # Test suite
```

## 🔧 API Endpoints

### Service Registration
- `POST /register` - Register new service
- `PUT /register/{service_id}` - Update service registration
- `DELETE /unregister/{service_id}` - Deregister service

### Service Discovery
- `GET /services` - List all registered services
- `GET /services/{service_type}` - List services by type
- `GET /discovery` - Get service discovery information
- `GET /discovery/{service_type}` - Discover services by capability

### Health Monitoring
- `GET /health` - Registry health check
- `GET /health/{service_id}` - Check specific service health
- `POST /health/{service_id}` - Report service health status

### Service Management
- `GET /services/{service_id}` - Get service details
- `PATCH /services/{service_id}` - Update service metadata
- `GET /metrics` - Registry metrics and statistics

## 🔐 Authentication

### JWT Authentication
- All endpoints require JWT authentication
- Service tokens with specific permissions
- Token validation and expiration checking
- Role-based access control (RBAC)

### Service-to-Service Auth
```bash
# Service registration with JWT
curl -X POST http://localhost:8001/register \
  -H "Authorization: Bearer SERVICE_JWT_TOKEN" \
  -d '{"id": "my-service", "endpoint": "http://localhost:3000"}'
```

## 📊 Service Registration Model

### Service Definition
```python
class ServiceRegistration(BaseModel):
    id: str                    # Unique service identifier
    name: str                  # Human-readable service name
    endpoint: str              # Primary service endpoint
    version: str               # Service version
    capabilities: List[str]    # Service capabilities
    health_check: Optional[str] # Health check endpoint
    metadata: Dict[str, Any]    # Additional metadata
    registered_at: datetime     # Registration timestamp
    last_heartbeat: datetime   # Last health check
    status: ServiceStatus       # Current status
```

### Service Status
- **ACTIVE**: Service is healthy and available
- **DEGRADED**: Service is running with limited capacity
- **INACTIVE**: Service is temporarily unavailable
- **TERMINATED**: Service has been shut down

## 🔧 Development Commands

```bash
# Development server
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Production server
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 2

# Testing
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest --cov=app          # With coverage

# Type checking
mypy .                    # Static type checking

# Linting
flake8 .                  # Code style checking
black .                   # Code formatting
```

## 🧪 Testing

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: Service registration and discovery flows
- **Health Check Tests**: Health monitoring functionality
- **Performance Tests**: Registry under load

### Running Tests
```bash
# All tests
pytest

# Test categories
pytest -m unit
pytest -m integration
pytest -m health

# Performance testing
pytest -m performance
```

## 🚀 Deployment

### Environment Variables
Required for production:

```bash
# Server Configuration
PORT=8001
HOST=0.0.0.0

# Security
SECRET_KEY=your_production_secret
JWT_ALGORITHM=HS256

# Storage
STORAGE_BACKEND=memory    # memory, redis, etcd
REDIS_URL=redis://localhost:6379
ETCD_HOST=localhost:2379

# Health Monitoring
HEALTH_CHECK_INTERVAL=30
SERVICE_EXPIRATION=300
CLEANUP_INTERVAL=60
```

### Docker Deployment
```dockerfile
# Build image
docker build -t kyros-service-registry .

# Run container
docker run -p 8001:8001 \
  -e SECRET_KEY=your_secret \
  -e STORAGE_BACKEND=memory \
  kyros-service-registry
```

### Docker Compose
```yaml
services:
  service-registry:
    build: ./packages/service-registry
    ports:
      - "8001:8001"
    environment:
      - SECRET_KEY=your_secret
      - STORAGE_BACKEND=redis
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
```

## 🔧 Troubleshooting

### Common Issues

**Service Registration Issues**
```bash
# Check registry health
curl http://localhost:8001/health

# Check registered services
curl -H "Authorization: Bearer TOKEN" http://localhost:8001/services

# Test service registration
curl -X POST http://localhost:8001/register \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id":"test","endpoint":"http://test:8000"}'
```

**Health Check Issues**
1. Verify health check endpoints are accessible
2. Check network connectivity between services
3. Monitor service expiration settings
4. Review health check interval configuration

**Storage Backend Issues**
```bash
# Redis connectivity test
redis-cli ping

# etcd connectivity test (if using)
etcdctl endpoint health

# Check storage configuration
curl http://localhost:8001/metrics
```

### Debug Mode
Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

## 📊 Monitoring & Observability

### Registry Metrics
- Total registered services
- Service registration/unregistration rates
- Health check success/failure rates
- Storage backend performance

### Service Health Metrics
- Service availability percentages
- Average response times
- Failure rates by service type
- Capacity utilization metrics

### Logging
- Service registration events
- Health check results
- Storage operation logs
- Error tracking with stack traces

## 🛡️ Security Considerations

### Authentication Security
- Strong JWT secrets with proper rotation
- Token expiration and refresh mechanisms
- Service-specific access permissions
- Audit logging for all operations

### Network Security
- TLS encryption for all communications
- Firewall rules restricting access
- Network segmentation between service tiers
- Rate limiting on registration endpoints

### Data Security
- Sensitive data encryption at rest
- Secure credential storage
- Input validation and sanitization
- Audit trail for all modifications

## 🔮 Future Enhancements

### Distributed Storage
- **etcd Integration**: Replace in-memory storage with etcd
- **High Availability**: Multi-node registry clustering
- **Consensus Algorithms**: Raft consensus for consistency
- **Leader Election**: Automatic leader failover

### Advanced Features
- **Service Mesh Integration**: Istio/Linkerd support
- **Auto-scaling**: Dynamic instance registration
- **Canary Deployments**: Gradual rollout coordination
- **Circuit Breaking**: Fault tolerance patterns

## 📚 Client Libraries

### Python Client
```python
import requests

class ServiceRegistryClient:
    def __init__(self, registry_url, auth_token):
        self.registry_url = registry_url
        self.headers = {"Authorization": f"Bearer {auth_token}"}
    
    def register_service(self, service_data):
        response = requests.post(
            f"{self.registry_url}/register",
            json=service_data,
            headers=self.headers
        )
        return response.json()
    
    def discover_services(self, service_type=None):
        url = f"{self.registry_url}/services"
        if service_type:
            url += f"/{service_type}"
        
        response = requests.get(url, headers=self.headers)
        return response.json()
```

### JavaScript Client
```javascript
class ServiceRegistryClient {
    constructor(registryUrl, authToken) {
        this.registryUrl = registryUrl;
        this.authToken = authToken;
    }
    
    async registerService(serviceData) {
        const response = await fetch(`${this.registryUrl}/register`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(serviceData)
        });
        return response.json();
    }
    
    async discoverServices(serviceType) {
        const url = serviceType 
            ? `${this.registryUrl}/services/${serviceType}`
            : `${this.registryUrl}/services`;
            
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${this.authToken}`
            }
        });
        return response.json();
    }
}
```

## 🔗 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [etcd Documentation](https://etcd.io/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [JWT Documentation](https://jwt.io/)
- [Service Discovery Patterns](https://microservices.io/patterns/service-registry.html)
- [Project Architecture](../../docs/architecture/overview.md)
- [API Documentation](../../docs/api/README.md)