import asyncio
import fcntl
import json
import logging
import os
import pty
import select
import struct
import termios
from typing import AsyncIterator
from uuid import uuid4

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse, StreamingResponse

from .auth import get_current_user_required
from .core.config import settings
from .crew_runner import run_crew
from .db.models import User
from .models import CancelRequest, Run, RunCreate, RunStatus
from .routers import auth, auth_refresh, auth_ws, batch_runs, memory, projects
from .storage import store

logger = logging.getLogger(__name__)

# Import middleware and utilities
try:
    from .middleware.rate_limit import rate_limiter
    from .middleware.error_handler import (
        validation_exception_handler,
        database_exception_handler,
        generic_exception_handler
    )
    from .middleware.metrics import MetricsMiddleware, get_metrics
    from .middleware.correlation import CorrelationIDMiddleware
    from .cache.redis_cache import cache
    from .jobs.cleanup import start_background_jobs, stop_background_jobs, get_job_status
    FEATURES_ENABLED = True
except ImportError as e:
    logger.warning(f"Some enhanced features not available: {e}")
    FEATURES_ENABLED = False


app = FastAPI(
    title="Kyros Praxis API (Multi-Agent Orchestration)",
    description="CrewAI-based multi-agent orchestration API with authentication and shared memory",
    version="0.3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add enhanced middleware if available
if FEATURES_ENABLED:
    # Add correlation ID middleware (first, so it's available in all logs)
    app.add_middleware(CorrelationIDMiddleware)
    
    # Add metrics middleware
    app.middleware("http")(MetricsMiddleware())
    
    # Add rate limiting middleware
    @app.middleware("http")
    async def rate_limit_middleware(request, call_next):
        try:
            await rate_limiter.check(request)
            response = await call_next(request)
            return response
        except HTTPException as e:
            return ORJSONResponse(
                status_code=e.status_code,
                content=e.detail
            )
    
    # Add exception handlers
    from fastapi.exceptions import RequestValidationError
    from sqlalchemy.exc import SQLAlchemyError
    
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

# Include routers
app.include_router(auth.router)
app.include_router(auth_refresh.router)
app.include_router(auth_ws.router)
app.include_router(projects.router)
app.include_router(batch_runs.router)
app.include_router(memory.router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Kyros Praxis API...")
    
    # Validate production configuration
    if settings.KYROS_ENV == "production":
        logger.info("Production mode detected - validating configuration...")
        
        # Check JWT secret key
        if not settings.JWT_SECRET_KEY or len(settings.JWT_SECRET_KEY) < 32:
            raise RuntimeError(
                "CRITICAL: JWT_SECRET_KEY must be set and at least 32 characters in production. "
                "Generate with: openssl rand -hex 32"
            )
        
        # Check database URL is not default
        if "localhost" in settings.DATABASE_URL:
            logger.warning("WARNING: Using localhost database in production mode")
        
        # Ensure CORS is not wide open
        if "*" in settings.CORS_ALLOW_ORIGINS:
            raise RuntimeError(
                "CRITICAL: CORS_ALLOW_ORIGINS cannot be '*' in production. "
                "Specify exact origins."
            )
        
        # Check if DEBUG is disabled
        if settings.DEBUG:
            logger.warning("WARNING: DEBUG mode is enabled in production")
        
        logger.info("Production configuration validated ✓")
    
    if FEATURES_ENABLED:
        # Connect to Redis cache
        await cache.connect()
        
        # Start background jobs
        start_background_jobs()
        
        logger.info("Enhanced features enabled: rate limiting, metrics, caching, background jobs")
    else:
        logger.warning("Running with basic features only")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Kyros Praxis API...")
    
    if FEATURES_ENABLED:
        # Stop background jobs
        stop_background_jobs()
        
        # Disconnect from Redis
        await cache.disconnect()
        
        logger.info("Enhanced features stopped")


@app.get("/health", response_class=ORJSONResponse)
async def health():
    """Health check endpoint."""
    health_data = {
        "status": "ok",
        "env": settings.KYROS_ENV
    }
    
    if FEATURES_ENABLED:
        health_data["features"] = {
            "rate_limiting": True,
            "metrics": True,
            "caching": cache.enabled,
            "background_jobs": True
        }
    
    return health_data


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    if not FEATURES_ENABLED:
        raise HTTPException(status_code=404, detail="Metrics not available")
    return get_metrics()


@app.get("/admin/jobs", response_class=ORJSONResponse)
async def get_jobs():
    """Get status of background jobs."""
    if not FEATURES_ENABLED:
        raise HTTPException(status_code=404, detail="Background jobs not available")
    return {"jobs": get_job_status()}


@app.get("/admin/providers", response_class=ORJSONResponse)
async def get_providers():
    """Get status of configured LLM providers."""
    from .llm_providers import list_available_providers, validate_provider_config
    
    providers = list_available_providers()
    current = settings.MODEL_PROVIDER
    current_validation = validate_provider_config(current)
    
    return {
        "current_provider": current,
        "current_model": settings.MODEL_NAME,
        "current_valid": current_validation["valid"],
        "current_missing": current_validation["missing"],
        "providers": providers
    }


@app.post("/crews/runs", response_model=Run, response_class=ORJSONResponse)
async def create_run(
    req: RunCreate,
    bg: BackgroundTasks,
    current_user: User = Depends(get_current_user_required)
):
    """Create a crew run. Requires authentication."""
    run = await store.create_run(crew_id=req.crew_id, payload=req.input)
    bg.add_task(run_crew, run.id, req.crew_id, req.input)
    return run


@app.get("/crews/runs/{run_id}", response_model=Run, response_class=ORJSONResponse)
async def get_run(
    run_id: str,
    current_user: User = Depends(get_current_user_required)
):
    """Get a run by ID. Requires authentication."""
    rec = await store.get_run(run_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Run not found")
    return rec.run


@app.post("/crews/runs/{run_id}/cancel", response_class=ORJSONResponse)
async def cancel_run(
    run_id: str,
    body: CancelRequest | None = None,
    current_user: User = Depends(get_current_user_required)
):
    """Cancel a run. Requires authentication."""
    ok = await store.cancel(run_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"status": "accepted", "run_id": run_id, "reason": getattr(body, "reason", None)}


async def sse_iter(run_id: str) -> AsyncIterator[bytes]:
    terminal = {RunStatus.succeeded, RunStatus.failed, RunStatus.canceled}
    last_id = 0

    status = await store.get_status(run_id)
    if status is None:
        yield b"event: error\n" + b"data: \"Run not found\"\n\n"
        return

    while True:
        events = await store.list_events_since(run_id, last_id)
        for ev in events:
            last_id = ev["id"]
            payload = {k: v for k, v in ev.items() if k != "id"}
            data = json.dumps(payload)
            yield b"event: message\n" + f"data: {data}\n\n".encode()

        status = await store.get_status(run_id)
        if status is None:
            yield b"event: error\n" + b"data: \"Run not found\"\n\n"
            return
        if status in terminal and not events:
            break
        await asyncio.sleep(0.5)


@app.get("/crews/runs/{run_id}/events")
async def get_run_events(
    run_id: str,
    current_user: User = Depends(get_current_user_required)
):
    """Get run events via SSE. Requires authentication."""
    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive"}
    return StreamingResponse(sse_iter(run_id), media_type="text/event-stream", headers=headers)


# Terminal WebSocket support
MAX_TERMINALS = settings.MAX_TERMINAL_CONNECTIONS
active_terminals: dict[str, dict] = {}


@app.websocket("/ws/terminal")
async def terminal_websocket(websocket: WebSocket, token: str = None):
    """
    WebSocket endpoint for terminal PTY.
    Provides a real bash shell over WebSocket with JWT authentication.
    
    SECURITY: Authenticates user BEFORE accepting WebSocket connection.
    
    Args:
        websocket: WebSocket connection
        token: JWT token (required in query parameter)
    """
    from .auth import get_current_user_from_token
    from .db.session import AsyncSessionLocal
    
    terminal_id = str(uuid4())
    
    # Check concurrent connection limit
    if len(active_terminals) >= MAX_TERMINALS:
        await websocket.close(code=1008, reason="Too many terminals")
        logger.warning("Terminal connection rejected: limit reached")
        return
    
    # SECURITY FIX: Authenticate BEFORE accepting connection
    # This prevents resource exhaustion from unauthenticated connections
    authenticated_user = None
    
    # Require token in query parameter (can't read messages before accept)
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        logger.warning(f"Terminal {terminal_id}: No token provided")
        return
    
    # Validate token before accepting connection
    try:
        async with AsyncSessionLocal() as session:
            authenticated_user = await get_current_user_from_token(token, session)
        
        if not authenticated_user:
            await websocket.close(code=1008, reason="Invalid token")
            logger.warning(f"Terminal {terminal_id}: Invalid token")
            return
    except Exception as e:
        await websocket.close(code=1008, reason="Authentication failed")
        logger.warning(f"Terminal {terminal_id}: Auth failed: {e}")
        return
    
    # Only accept connection after successful authentication
    await websocket.accept()
    logger.info(f"Terminal {terminal_id} WebSocket ACCEPTED for user {authenticated_user.username} (ID: {authenticated_user.id})")
    
    # Send auth success confirmation
    await websocket.send_json({
        "type": "auth_success",
        "user": {"id": authenticated_user.id, "username": authenticated_user.username}
    })
    
    logger.info(f"Terminal {terminal_id}: Authenticated as {authenticated_user.username} (ID: {authenticated_user.id})")
    
    # Add to active terminals
    active_terminals[terminal_id] = {"user_id": authenticated_user.id, "username": authenticated_user.username}
    logger.info(f"Terminal {terminal_id} STARTING (total: {len(active_terminals)})")
    
    pid = None
    fd = None
    
    try:
        # Fork PTY
        logger.info(f"Terminal {terminal_id}: Forking PTY...")
        pid, fd = pty.fork()
        
        if pid == 0:
            # Child process - exec bash
            env = os.environ.copy()
            env['TERM'] = 'xterm-256color'
            env['COLORTERM'] = 'truecolor'
            env['PS1'] = '\\u@\\h:\\w\\$ '
            # Start bash in interactive mode
            os.execvpe("/bin/bash", ["/bin/bash", "-i"], env)
        
        logger.info(f"Terminal {terminal_id}: PTY forked, pid={pid}, fd={fd}")
        
        # Parent process - handle I/O
        # Set non-blocking mode
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        
        async def read_output():
            """Read from PTY and send to WebSocket."""
            try:
                while True:
                    try:
                        # Check if data available with minimal timeout for responsiveness
                        r, _, _ = select.select([fd], [], [], 0.001)  # 1ms timeout for low latency
                        if r:
                            try:
                                output = os.read(fd, 10240)
                                if output:
                                    await websocket.send_bytes(output)
                                else:
                                    # EOF - shell exited
                                    logger.info(f"Terminal {terminal_id}: shell exited (EOF)")
                                    break
                            except OSError as e:
                                # PTY closed
                                logger.info(f"Terminal {terminal_id}: PTY closed: {e}")
                                break
                        else:
                            # No data available, yield to other tasks briefly
                            await asyncio.sleep(0.001)  # 1ms sleep instead of 10ms
                    except ValueError as e:
                        # File descriptor was closed
                        logger.info(f"Terminal {terminal_id}: fd closed: {e}")
                        break
            except Exception as e:
                import traceback
                logger.error(f"Terminal {terminal_id}: read_output error: {e}, traceback: {traceback.format_exc()}")
        
        async def write_input():
            """Read from WebSocket and write to PTY."""
            try:
                while True:
                    data = await websocket.receive()
                    
                    if "bytes" in data:
                        # Binary data (normal input)
                        os.write(fd, data["bytes"])
                    elif "text" in data:
                        # Text data (convert to bytes)
                        text = data["text"]
                        if text:
                            # Check if it's a JSON control message
                            try:
                                msg = json.loads(text)
                                if msg.get("type") == "resize":
                                    # Handle terminal resize
                                    rows = msg.get("rows", 24)
                                    cols = msg.get("cols", 80)
                                    size = struct.pack("HHHH", rows, cols, 0, 0)
                                    fcntl.ioctl(fd, termios.TIOCSWINSZ, size)
                                    logger.debug(f"Terminal {terminal_id}: resized to {rows}x{cols}")
                            except (json.JSONDecodeError, ValueError):
                                # Not JSON, treat as normal text
                                os.write(fd, text.encode())
                    
            except WebSocketDisconnect:
                logger.info(f"Terminal {terminal_id}: client disconnected")
            except Exception as e:
                logger.error(f"Terminal {terminal_id}: write_input error: {e}")
        
        # Run both I/O tasks simultaneously
        await asyncio.gather(
            read_output(),
            write_input(),
            return_exceptions=True
        )
    
    except Exception as e:
        logger.error(f"Terminal {terminal_id}: websocket error: {e}", exc_info=True)
    
    finally:
        # Cleanup
        if pid is not None:
            try:
                os.kill(pid, 9)  # Kill child process
                logger.debug(f"Terminal {terminal_id}: killed process {pid}")
            except ProcessLookupError:
                pass  # Already dead
            except Exception as e:
                logger.error(f"Terminal {terminal_id}: error killing process: {e}")
        
        if fd is not None:
            try:
                os.close(fd)
                logger.debug(f"Terminal {terminal_id}: closed PTY fd")
            except OSError:
                pass  # Already closed
        
        try:
            await websocket.close()
        except Exception:
            pass  # Already closed
        
        active_terminals.discard(terminal_id)
        logger.info(f"Terminal {terminal_id} disconnected (remaining: {len(active_terminals)})")

