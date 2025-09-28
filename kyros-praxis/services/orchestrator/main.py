"""
Main entry point for the Kyros Orchestrator service.

This module initializes the FastAPI application, configures middleware, sets up
authentication, and mounts all API routers. It also handles global exception
handling, health checks, and WebSocket connections.

The orchestrator serves as the central coordination point for Kyros services,
managing job scheduling, task collaboration, event handling, and security.

MODULE RESPONSIBILITIES:
------------------------
1. FastAPI Application Setup:
   - Initializes the FastAPI application with project metadata
   - Configures OpenAPI documentation settings
   - Sets up global exception handlers for HTTP and general exceptions

2. Security Configuration:
   - Implements JWT-based authentication and authorization
   - Configures rate limiting with SlowAPI
   - Sets up security middleware for CSRF protection and HTTPS enforcement
   - Integrates with auth.py for user authentication flows

3. API Routing:
   - Mounts all API routers for jobs, tasks, events, and utilities
   - Configures WebSocket endpoints for real-time communication
   - Sets up health check endpoints

4. Middleware Integration:
   - Applies security middleware for comprehensive protection
   - Configures rate limiting middleware
   - Adds request logging middleware for monitoring

5. Database Integration:
   - Connects to database through database.py dependency injection
   - Provides health check endpoints that verify database connectivity

INTEGRATION FLOW:
-----------------
1. Application startup loads configuration from environment variables
2. Security middleware is configured with settings from security_middleware.py
3. Database connections are established through database.py
4. API routers are mounted with appropriate prefixes and tags
5. Authentication system is initialized using auth.py components
6. WebSocket connections are configured with JWT authentication
7. All components are integrated into the main FastAPI application

USAGE:
------
To run the orchestrator service:
    uvicorn main:app --host 0.0.0.0 --port 8000

The service will be available at http://localhost:8000 with API documentation
at http://localhost:8000/docs

SECURITY FEATURES:
------------------
- JWT-based authentication with secure token expiration
- Rate limiting to prevent abuse
- CSRF protection for state-changing operations
- HTTPS enforcement in production environments
- Comprehensive exception handling to prevent information leakage
- Security headers for XSS, CSRF, and content sniffing protection

See Also:
--------
- auth.py: Authentication and user management
- database.py: Database configuration and session management
- security_middleware.py: Security middleware implementation
- models.py: Database models for jobs, events, tasks, and users
"""

from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import logging

# Load environment variables from .env file
load_dotenv()

# Setup logging with ORCH_ID support
try:
    from .app.core.logging import setup_logging, setup_orchestrator_logging
    from .app.core.config import settings
except ImportError:
    from app.core.logging import setup_logging, setup_orchestrator_logging  # type: ignore
    from app.core.config import settings  # type: ignore

# Get ORCH_ID from settings or environment
orch_id = getattr(settings, 'ORCH_ID', os.getenv("ORCH_ID", "o-glm"))
log_file = os.getenv("ORCH_LOG_FILE", f".devlogs/orch-{orch_id}.log")

# Initialize standard logging configuration
setup_logging(
    log_level=getattr(settings, 'LOG_LEVEL', os.getenv("LOG_LEVEL", "INFO")),
    log_file=log_file
)

# Setup orchestrator event logging for SSE
setup_orchestrator_logging(orch_id, log_file)

# Setup logger
logger = logging.getLogger(__name__)
logger.info(f"Orchestrator starting with ORCH_ID: {orch_id}")

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    WebSocket,
    status,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse

# Rate limiting imports
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    HAVE_SLOWAPI = True
except ImportError:
    Limiter = None
    _rate_limit_exceeded_handler = None
    get_remote_address = None
    RateLimitExceeded = Exception
    SlowAPIMiddleware = None
    HAVE_SLOWAPI = False
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,  # noqa: F401 (placeholder for future async endpoints)
)

# Import modules directly without relative imports
from auth import (  # type: ignore
    User,
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user,
    Login,
)
from database import get_db  # type: ignore
import routers.events as events  # type: ignore
import routers.jobs as jobs  # type: ignore
import routers.tasks as tasks  # type: ignore
import routers.agents as agents  # type: ignore
from app.core.config import settings  # type: ignore
from security_middleware import setup_security, SecurityConfig  # type: ignore

# Use the API_V1_STR from settings
API_V1_STR = settings.API_V1_STR

# Initialize the FastAPI application with project metadata
app = FastAPI(
    title=settings.PROJECT_NAME + " - Orchestrator API",
    version=settings.VERSION,
    openapi_url=f"{API_V1_STR}/openapi.json",
    description="""
    The Kyros Orchestrator API manages job scheduling, task collaboration, and event handling
    across the Kyros ecosystem. It provides RESTful endpoints for managing workflows,
    monitoring system health, and coordinating distributed tasks.
    
    Key features:
    - Job scheduling and management
    - Task collaboration and coordination
    - Event handling and streaming
    - Authentication and authorization
    - Health monitoring and diagnostics
    """,
    contact={
        "name": "Kyros Development Team",
        "url": "https://kyros-praxis.com",
        "email": "support@kyros-praxis.com",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://kyros-praxis.com/license",
    },
)

# Setup rate limiting with SlowAPI
if HAVE_SLOWAPI:
    # Create limiter with JWT-aware key function
    def jwt_limiter_key_func(request):
        """Rate limiting key function that uses JWT user ID when available."""
        try:
            # Try to extract user ID from JWT token
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                from jose import jwt
                token = auth_header.split(" ")[1]
                payload = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM],
                    options={"verify_exp": False}  # Don't verify expiration for rate limiting
                )
                user_id = payload.get("sub")
                if user_id:
                    return f"user:{user_id}"
        except Exception:
            pass

        # Fall back to IP address
        return f"ip:{get_remote_address(request)}"

    limiter = Limiter(key_func=jwt_limiter_key_func)

    # Add rate limiting middleware
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
else:
    logger.warning("SlowAPI not available, rate limiting disabled")

# Setup security middleware
# Configure security settings based on application environment
security_config = SecurityConfig(
    jwt_secret=settings.SECRET_KEY,
    csrf_secret=settings.SECRET_KEY + "_csrf",  # Derive CSRF secret from main secret
    jwt_algorithm=settings.JWT_ALGORITHM,
    jwt_expiration_hours=settings.ACCESS_TOKEN_EXPIRE_MINUTES // 60,
    backend_cors_origins=settings.all_cors_origins,
    force_https=settings.ENVIRONMENT != "local",
    secure_cookies=settings.ENVIRONMENT != "local",
    environment=settings.ENVIRONMENT,
    redis_url=getattr(settings, 'redis_url', None),
    csrf_enabled=settings.ENVIRONMENT != "local",  # Disable CSRF for local/test environment
)

# Apply security middleware to the FastAPI application
setup_security(app, security_config)

# Add custom exception handlers for structured error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions with structured responses.
    
    Converts FastAPI HTTPException into a consistent JSON error format
    that includes request context for better debugging.
    
    Args:
        request (Request): The incoming HTTP request
        exc (HTTPException): The raised HTTP exception
        
    Returns:
        JSONResponse: Structured error response with error details
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_exception",
                "code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path),
                "method": request.method,
            }
        },
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle general exceptions with structured responses.
    
    Catches all unhandled exceptions and converts them into a consistent
    JSON error format. Logs the full exception for debugging purposes.
    
    Args:
        request (Request): The incoming HTTP request
        exc (Exception): The raised exception
        
    Returns:
        JSONResponse: Structured error response with error details
    """
    # Log the error with full context and traceback
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "error_type": type(exc).__name__,
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "internal_server_error",
                "code": 500,
                "message": "An internal server error occurred",
                "path": str(request.url.path),
                "method": request.method,
            }
        },
    )

# Add request logging middleware
# This middleware logs all incoming requests for monitoring and debugging
try:
    from .middleware import logging as logging_middleware
    app.add_middleware(logging_middleware.RequestLoggingMiddleware)
except Exception:  # Fallback when running module directly
    try:
        import middleware.logging as logging_middleware  # type: ignore
        app.add_middleware(logging_middleware.RequestLoggingMiddleware)
    except ImportError:
        # If middleware directory doesn't exist, skip logging middleware
        pass

# API v1 routers (mount once at /api/v1; routers define their own paths)
# Mount all API routers with appropriate tags for OpenAPI documentation
app.include_router(jobs.router, prefix=f"{API_V1_STR}", tags=["jobs"])
app.include_router(tasks.router, prefix=f"{API_V1_STR}", tags=["collab"])
app.include_router(events.router, prefix=f"{API_V1_STR}", tags=["events"])
app.include_router(agents.router, prefix=f"{API_V1_STR}", tags=["agents"])

# Include utils router for utility functions
try:
    from .routers import utils as _utils
except Exception:  # Fallback when running module directly
    import routers.utils as _utils  # type: ignore
app.include_router(_utils.router, prefix=f"{API_V1_STR}", tags=["utils"])

# Include security and monitoring routers
try:
    from .routers import security, monitoring
except Exception:  # Fallback when running module directly
    import routers.security as security  # type: ignore
    import routers.monitoring as monitoring  # type: ignore
app.include_router(security.router, prefix=f"{API_V1_STR}", tags=["security"])
app.include_router(monitoring.router, prefix=f"{API_V1_STR}", tags=["monitoring"])

# Include orchestrator events router for orchestrator-specific events
try:
    from .routers import orchestrator_events
except Exception:  # Fallback when running module directly
    import routers.orchestrator_events as orchestrator_events  # type: ignore
app.include_router(orchestrator_events.router, prefix=f"{API_V1_STR}", tags=["orchestrator-events"])

# events router included above


@app.get("/", summary="Root endpoint", description="Returns a simple message indicating the API is running")
async def root() -> dict:
    """
    Root endpoint.
    
    Returns a simple message indicating that the Orchestrator API is running.
    
    Returns:
        dict: A dictionary with a message indicating the API status
    """
    return {"message": "Orchestrator API is running"}


@app.get("/health", summary="Health check", description="Returns the health status of the orchestrator service")
async def health() -> dict:
    """
    Health check.
    
    Simple health check endpoint that returns the status of the orchestrator service.
    
    Returns:
        dict: A dictionary with the service status
    """
    return {"status": "healthy"}


@app.get("/healthz", summary="Database health check", description="Returns the health status of the orchestrator service and its database connection")
def healthz(db=Depends(get_db)) -> dict:
    """
    Health check with DB ping.
    
    Performs a health check that includes verifying the database connection
    by executing a simple SQL query.
    
    Args:
        db: Database session dependency
        
    Returns:
        dict: A dictionary with the service and database status
        
    Raises:
        HTTPException: If the database is unavailable (status code 500)
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=500, detail="DB unavailable")


@app.post("/auth/login", summary="User login", description="Authenticates a user and returns a JWT access token")
async def login(payload: Login, db=Depends(get_db)) -> dict:
    """
    Login endpoint (JSON body).
    
    Authenticates a user with username and password, and returns a JWT access token
    for subsequent authenticated requests.
    
    Args:
        payload (Login): Login credentials containing username and password
        db: Database session dependency for user authentication
        
    Returns:
        dict: A dictionary containing the access token and token type
        
    Raises:
        HTTPException: If authentication fails (status code 401)
    """
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    Enhanced WebSocket endpoint with JWT authentication.
    
    Handles real-time communication with authenticated clients. Authentication
    can be provided via query parameter or Authorization header.
    
    Message Flow:
    1. Client connects with JWT token
    2. Server validates token and accepts connection
    3. Server sends connection confirmation
    4. Server echoes messages back with metadata
    5. Connection closes when client disconnects or on error
    
    Args:
        websocket (WebSocket): The WebSocket connection object
        
    Raises:
        WebSocketDisconnect: When the client disconnects
        Exception: For unexpected errors during communication
    """
    # Extract token from query parameter or header
    token = None
    if "token" in websocket.query_params:
        token = websocket.query_params["token"]
    elif "authorization" in websocket.headers:
        auth_header = websocket.headers["authorization"]
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    # Validate token
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication token")
        return

    try:
        # Use the same JWT validation as HTTP endpoints
        from jose import jwt
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
            options={
                "require": ["sub", "iss", "aud"],
                "verify_iss": True,
                "verify_aud": True,
                "verify_exp": True,
                "verify_iat": True,
            }
        )
        username = payload.get("sub")
        if not username:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return
    except Exception as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=f"Authentication failed: {str(e)}")
        return

    # Accept connection after authentication
    await websocket.accept()

    # Send initial connection success message
    await websocket.send_json({
        "type": "connection",
        "status": "connected",
        "user": username,
        "timestamp": datetime.utcnow().isoformat()
    })

    try:
        while True:
            # Receive and validate message
            try:
                data = await websocket.receive_json()

                # Basic message validation
                if not isinstance(data, dict):
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid message format: must be JSON object"
                    })
                    continue

                # Echo back with metadata
                response = {
                    "type": "message",
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat(),
                    "user": username
                }
                await websocket.send_json(response)

            except ValueError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })

    except WebSocketDisconnect:
        # Client disconnected
        pass
    except Exception as e:
        # Log unexpected errors
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
