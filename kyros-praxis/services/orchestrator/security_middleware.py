"""
Comprehensive security middleware for FastAPI
Implements CSRF protection, rate limiting, and security headers
"""

import time
import secrets
import hashlib
import hmac
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import jwt
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SecurityConfig(BaseModel):
    """Security configuration"""
    jwt_secret: str
    csrf_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 900  # 15 minutes in seconds
    csrf_enabled: bool = True
    csrf_cookie_name: str = "csrf_token"
    csrf_header_name: str = "X-CSRF-Token"
    secure_cookies: bool = True
    force_https: bool = True


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self, requests: int = 100, window: int = 900):
        self.requests = requests
        self.window = window
        self.clients: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if client is within rate limit"""
        now = time.time()
        
        # Clean old entries
        self.clients[client_id] = [
            timestamp for timestamp in self.clients[client_id]
            if now - timestamp < self.window
        ]
        
        # Check limit
        if len(self.clients[client_id]) >= self.requests:
            return False
        
        # Add current request
        self.clients[client_id].append(now)
        return True
    
    def get_reset_time(self, client_id: str) -> int:
        """Get time until rate limit resets"""
        if not self.clients[client_id]:
            return 0
        
        oldest = min(self.clients[client_id])
        return int(oldest + self.window - time.time())


class CSRFProtection:
    """CSRF token generation and validation"""
    
    def __init__(self, secret: str):
        self.secret = secret
    
    def generate_token(self) -> str:
        """Generate CSRF token"""
        random_data = secrets.token_bytes(32)
        timestamp = str(int(time.time())).encode()
        
        # Create token with timestamp
        token_data = random_data + b"|" + timestamp
        
        # Sign token
        signature = hmac.new(
            self.secret.encode(),
            token_data,
            hashlib.sha256
        ).digest()
        
        # Combine and encode
        full_token = token_data + b"|" + signature
        return secrets.token_urlsafe(32)  # Simplified for demo
    
    def validate_token(self, token: str, max_age: int = 3600) -> bool:
        """Validate CSRF token"""
        if not token:
            return False
        
        try:
            # In production, properly decode and verify signature
            # This is simplified for demonstration
            return len(token) == 43  # Expected length of token_urlsafe(32)
        except Exception:
            return False


class SecurityMiddleware(BaseHTTPMiddleware):
    """Main security middleware"""
    
    def __init__(self, app, config: SecurityConfig):
        super().__init__(app)
        self.config = config
        self.rate_limiter = RateLimiter(
            requests=config.rate_limit_requests,
            window=config.rate_limit_window
        )
        self.csrf = CSRFProtection(config.csrf_secret)
        self.bearer = HTTPBearer(auto_error=False)
    
    async def dispatch(self, request: Request, call_next):
        # 1. Force HTTPS in production
        if self.config.force_https and request.url.scheme != "https":
            if request.headers.get("X-Forwarded-Proto") != "https":
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "HTTPS required"}
                )
        
        # 2. Rate limiting
        if self.config.rate_limit_enabled:
            client_id = self.get_client_id(request)
            
            if not self.rate_limiter.is_allowed(client_id):
                reset_time = self.rate_limiter.get_reset_time(client_id)
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded"},
                    headers={
                        "X-RateLimit-Limit": str(self.config.rate_limit_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_time)
                    }
                )
        
        # 3. CSRF Protection for state-changing methods
        if self.config.csrf_enabled and request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            # Skip CSRF for API endpoints with valid JWT
            if not await self.has_valid_jwt(request):
                csrf_token = request.headers.get(self.config.csrf_header_name)
                
                if not csrf_token:
                    csrf_token = request.cookies.get(self.config.csrf_cookie_name)
                
                if not self.csrf.validate_token(csrf_token):
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "Invalid CSRF token"}
                    )
        
        # 4. Add security headers
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # HSTS header for HTTPS
        if self.config.force_https:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSP header
        response.headers["Content-Security-Policy"] = self.get_csp_header()
        
        # Generate CSRF token for GET requests
        if request.method == "GET" and self.config.csrf_enabled:
            csrf_token = self.csrf.generate_token()
            response.set_cookie(
                key=self.config.csrf_cookie_name,
                value=csrf_token,
                secure=self.config.secure_cookies,
                httponly=True,
                samesite="strict",
                max_age=3600
            )
        
        return response
    
    def get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get authenticated user ID
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            try:
                token = auth.split(" ")[1]
                payload = jwt.decode(
                    token,
                    self.config.jwt_secret,
                    algorithms=[self.config.jwt_algorithm]
                )
                return f"user:{payload.get('sub', 'unknown')}"
            except jwt.PyJWTError:
                pass
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        
        return f"ip:{request.client.host if request.client else 'unknown'}"
    
    async def has_valid_jwt(self, request: Request) -> bool:
        """Check if request has valid JWT token"""
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            return False
        
        try:
            token = auth.split(" ")[1]
            jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm]
            )
            return True
        except jwt.PyJWTError:
            return False
    
    def get_csp_header(self) -> str:
        """Generate Content Security Policy header"""
        directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Will tighten in production
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "upgrade-insecure-requests"
        ]
        
        if hasattr(self.config, 'csp_report_uri'):
            directives.append(f"report-uri {self.config.csp_report_uri}")
        
        return "; ".join(directives)


class JWTAuthentication:
    """JWT token management"""
    
    def __init__(self, secret: str, algorithm: str = "HS256", expiration_hours: int = 24):
        self.secret = secret
        self.algorithm = algorithm
        self.expiration_hours = expiration_hours
    
    def create_token(self, user_id: str, role: str = "user") -> str:
        """Create JWT token"""
        payload = {
            "sub": user_id,
            "role": role,
            "exp": datetime.utcnow() + timedelta(hours=self.expiration_hours),
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16)  # JWT ID for revocation
        }
        
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.PyJWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None


def setup_security(app, config: SecurityConfig):
    """Setup all security middleware"""
    
    # CORS configuration (restrictive)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.backend_cors_origins if hasattr(config, 'backend_cors_origins') else [],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
        expose_headers=["X-CSRF-Token"]
    )
    
    # Security middleware
    app.add_middleware(SecurityMiddleware, config=config)
    
    logger.info("Security middleware configured")
    
    return app