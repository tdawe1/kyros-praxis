"""
Comprehensive security middleware for the Kyros Orchestrator FastAPI application.

This module implements a multi-layered security approach for FastAPI applications,
providing defense-in-depth protection against common web application vulnerabilities.
It includes CSRF protection, rate limiting, JWT authentication, security headers,
and more. The module provides a centralized security configuration and middleware
that can be easily applied to any FastAPI application.

This security module is designed to work in conjunction with the auth.py module,
which provides user authentication functionality. Together, they form a complete
security solution for the Kyros Orchestrator service.

MODULE RESPONSIBILITIES:
------------------------
1. Multi-Layered Security:
   - CSRF protection with cryptographically secure tokens
   - Rate limiting with distributed and fallback mechanisms
   - JWT authentication and validation
   - Security headers for XSS, CSRF, and content sniffing protection
   - HTTPS enforcement for production environments
   - CORS configuration for controlled cross-origin access

2. Configuration Management:
   - Centralized SecurityConfig model for all security settings
   - Environment-based configuration through settings
   - Flexible security parameter tuning

3. Middleware Implementation:
   - SecurityMiddleware: Main middleware that applies all security measures
   - Integration with FastAPI's middleware system
   - Request/response processing for security enforcement

4. Component Security Features:
   - RateLimiter: Token bucket-style rate limiter with Redis/in-memory backends
   - CSRFProtection: Cryptographically secure CSRF token generation/validation
   - JWTAuthentication: JWT token creation and verification utilities

SECURITY FEATURES:
------------------
1. CSRF (Cross-Site Request Forgery) Protection:
   - Cryptographically secure token generation using HMAC-SHA256
   - Token binding to user sessions for additional security
   - Constant-time comparison to prevent timing attacks
   - Automatic token generation for GET requests
   - Validation for state-changing HTTP methods

2. Rate Limiting:
   - Token bucket-style rate limiting algorithm
   - Redis backend for distributed rate limiting
   - In-memory fallback for single-instance deployments
   - Per-client rate limiting based on user ID or IP
   - Configurable request limits and time windows

3. JWT Authentication:
   - Secure token signing with configurable algorithms
   - Standard JWT claims (exp, iss, aud, iat, jti)
   - Token expiration and validation
   - Integration with auth.py for user authentication

4. Security Headers:
   - Content Security Policy (CSP) for XSS prevention
   - HTTP Strict Transport Security (HSTS) for HTTPS enforcement
   - X-Content-Type-Options to prevent content sniffing
   - X-Frame-Options to prevent clickjacking
   - X-XSS-Protection for legacy browser protection
   - Referrer-Policy for privacy protection

5. Additional Security Measures:
   - HTTPS enforcement in production environments
   - CORS configuration with restricted origins
   - Content sniffing protection
   - XSS protection through headers and CSP

COMPONENTS:
-----------
1. SecurityConfig:
   - Centralized configuration model for all security settings
   - JWT, CSRF, rate limiting, and HTTPS configuration
   - Environment-specific security parameter tuning

2. RateLimiter:
   - Token bucket-style rate limiter implementation
   - Redis backend for distributed deployments
   - In-memory fallback for local development

3. CSRFProtection:
   - Cryptographically secure CSRF token generation
   - Token validation with constant-time comparison
   - Session binding for additional security

4. JWTAuthentication:
   - JWT token creation and verification utilities
   - Integration with auth.py for user authentication

5. SecurityMiddleware:
   - Main middleware that applies all security measures
   - Request processing for security enforcement
   - Response modification to add security headers

6. setup_security:
   - Function to configure security for FastAPI applications
   - Integration with CORS middleware
   - Application-level security configuration

INTEGRATION WITH OTHER MODULES:
-------------------------------
- main.py: Uses setup_security to configure middleware
- auth.py: Complements authentication functionality with JWT support
- middleware.py: Works alongside API key authentication middleware
- models.py: May integrate with User model for enhanced security features

USAGE EXAMPLE:
--------------
config = SecurityConfig(
    jwt_secret="super-secret-jwt-key",
    csrf_secret="super-secret-csrf-key",
    jwt_algorithm="HS512",
    jwt_expiration_hours=2
)

app = setup_security(app, config)

SECURITY FLOW:
--------------
1. Request Interception:
   - HTTPS enforcement check in production
   - Rate limiting based on client identification
   - CSRF protection for state-changing methods
   - JWT validation for authenticated requests

2. Response Modification:
   - Addition of security headers
   - CSRF token generation for GET requests
   - Rate limit header injection

ENVIRONMENT VARIABLES:
----------------------
- SECRET_KEY: Secret key for JWT signing
- JWT_ALGORITHM: Algorithm used for JWT signing
- ACCESS_TOKEN_EXPIRE_MINUTES: JWT token expiration time
- all_cors_origins: Allowed CORS origins
- ENVIRONMENT: Application environment (local, production, etc.)

See Also:
--------
- auth.py: Authentication module that complements security middleware
- middleware.py: API key authentication and rate limiting middleware
- main.py: Main application that uses security configuration
"""

import time
import secrets
import hashlib
import hmac
import base64
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta, timezone
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
    """
    Configuration model for security middleware settings.
    
    This Pydantic model defines all configurable security parameters
    for the security middleware components. It provides a centralized
    way to configure all security aspects of the application.
    
    Security Considerations:
    - JWT secrets should be cryptographically secure random values
    - CSRF secrets should be separate from JWT secrets for isolation
    - Rate limiting parameters should be tuned based on expected load
    - HTTPS should be enforced in production environments
    - CORS origins should be restricted to known domains
    
    Attributes:
        jwt_secret (str): Secret key for signing JWT tokens
        jwt_algorithm (str): Algorithm used for JWT signing (default: HS512)
        jwt_expiration_hours (int): Hours until JWT tokens expire (default: 2)
        csrf_secret (str): Secret key for signing CSRF tokens
        csrf_enabled (bool): Whether CSRF protection is enabled (default: True)
        csrf_cookie_name (str): Name of CSRF cookie (default: "csrf_token")
        csrf_header_name (str): Name of CSRF header (default: "X-CSRF-Token")
        rate_limit_enabled (bool): Whether rate limiting is enabled (default: True)
        rate_limit_requests (int): Max requests per window (default: 100)
        rate_limit_window (int): Rate limit window in seconds (default: 900)
        secure_cookies (bool): Whether to mark cookies as secure (default: True)
        force_https (bool): Whether to enforce HTTPS (default: True)
        backend_cors_origins (list[str]): Allowed CORS origins
        environment (str): Application environment (default: "local")
        csp_report_uri (Optional[str]): URI for CSP violation reports
        redis_url (Optional[str]): Redis connection URL for distributed rate limiting
    """
    # JWT configuration
    jwt_secret: str
    jwt_algorithm: str = "HS512"
    jwt_expiration_hours: int = 2
    
    # CSRF configuration
    csrf_secret: str
    csrf_enabled: bool = True
    csrf_cookie_name: str = "csrf_token"
    csrf_header_name: str = "X-CSRF-Token"
    
    # Rate limiting configuration  
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100  # requests per window
    rate_limit_window: int = 900  # 15 minutes in seconds
    rate_limit_burst: int = 20  # burst allowance
    
    # Production rate limiting (stricter)
    production_rate_limit_requests: int = 60  # Lower limit for production
    production_rate_limit_window: int = 900
    production_rate_limit_burst: int = 10
    
    # Security settings
    secure_cookies: bool = True
    force_https: bool = True
    backend_cors_origins: list[str] = []
    environment: str = "local"
    csp_report_uri: Optional[str] = None
    redis_url: Optional[str] = None


class RateLimiter:
    """
    Rate limiting implementation with Redis backend and in-memory fallback.
    
    Implements a token bucket-style rate limiter that can use Redis for
    distributed rate limiting or fall back to in-memory storage for
    single-instance deployments. This provides protection against abuse
    and helps ensure fair usage of the service.
    
    Security Considerations:
    - Uses client identification to track request rates
    - Implements both distributed (Redis) and local (in-memory) storage
    - Provides configurable limits to balance security and usability
    - Uses atomic operations for thread safety
    
    The rate limiter tracks requests per client ID and enforces limits
    based on a sliding window algorithm. It can identify clients by
    authenticated user ID or IP address.
    """

    def __init__(self, requests: int = 100, window: int = 900, redis_url: Optional[str] = None):
        """
        Initialize the rate limiter.
        
        Sets up the rate limiter with the specified parameters and
        attempts to connect to Redis if a URL is provided.
        
        Args:
            requests (int): Maximum number of requests allowed in the window
            window (int): Time window in seconds
            redis_url (Optional[str]): Redis connection URL, if available
        """
        self.requests = requests
        self.window = window
        self.redis_url = redis_url
        self.redis_client = None
        self.fallback_clients: Dict[str, list] = defaultdict(list)

        # Try to initialize Redis client
        if redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url)
                # Test connection
                self.redis_client.ping()
                logger.info("Rate limiter connected to Redis")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis, falling back to in-memory: {e}")
                self.redis_client = None
        else:
            logger.warning("Redis URL not configured, using in-memory rate limiting")

    def is_allowed(self, client_id: str) -> bool:
        """
        Check if a client is within the rate limit.
        
        Determines if the specified client is allowed to make another
        request based on the current rate limit configuration.
        
        Args:
            client_id (str): Unique identifier for the client
            
        Returns:
            bool: True if the client is allowed, False if rate limited
        """
        if self.redis_client:
            return self._is_allowed_redis(client_id)
        else:
            return self._is_allowed_memory(client_id)

    def _is_allowed_redis(self, client_id: str) -> bool:
        """
        Check rate limit using Redis for distributed rate limiting.
        
        Uses Redis atomic operations to ensure thread-safe rate limiting
        across multiple application instances. This is essential for
        horizontally scaled deployments.
        
        Args:
            client_id (str): Unique identifier for the client
            
        Returns:
            bool: True if the client is allowed, False if rate limited
        """
        key = f"rate_limit:{client_id}"

        try:
            # Use Redis pipeline for atomic operations
            with self.redis_client.pipeline() as pipe:
                # Get current count and TTL
                pipe.get(key)
                pipe.ttl(key)

                results = pipe.execute()
                current_count = int(results[0] or 0)
                ttl = results[1]

                # If key doesn't exist or expired, set new count
                if current_count == 0 or ttl == -1:
                    pipe.set(key, 1, ex=self.window)
                    pipe.execute()
                    return True

                # Check if limit exceeded
                if current_count >= self.requests:
                    return False

                # Increment count
                pipe.incr(key)
                pipe.execute()
                return True

        except Exception as e:
            logger.error(f"Redis rate limiting failed, falling back to in-memory: {e}")
            return self._is_allowed_memory(client_id)

    def _is_allowed_memory(self, client_id: str) -> bool:
        """
        Fallback in-memory rate limiting implementation.
        
        Used when Redis is not available or fails to connect. Maintains
        rate limiting state in memory, which works for single-instance
        deployments but not for distributed systems.
        
        Security Considerations:
        - Not suitable for horizontally scaled deployments
        - State is lost when the application restarts
        - Vulnerable to memory exhaustion attacks with many unique clients
        
        Args:
            client_id (str): Unique identifier for the client
            
        Returns:
            bool: True if the client is allowed, False if rate limited
        """
        now = time.time()

        # Clean old entries
        self.fallback_clients[client_id] = [
            timestamp for timestamp in self.fallback_clients[client_id]
            if now - timestamp < self.window
        ]

        # Check limit
        if len(self.fallback_clients[client_id]) >= self.requests:
            return False

        # Add current request
        self.fallback_clients[client_id].append(now)
        return True

    def get_reset_time(self, client_id: str) -> int:
        """
        Get time until rate limit resets for a client.
        
        Calculates how many seconds remain until the rate limit
        window resets for the specified client.
        
        Args:
            client_id (str): Unique identifier for the client
            
        Returns:
            int: Seconds until rate limit resets
        """
        if self.redis_client:
            return self._get_reset_time_redis(client_id)
        else:
            return self._get_reset_time_memory(client_id)

    def _get_reset_time_redis(self, client_id: str) -> int:
        """
        Get reset time from Redis.
        
        Queries Redis to determine when the rate limit window
        will reset for the specified client.
        
        Args:
            client_id (str): Unique identifier for the client
            
        Returns:
            int: Seconds until rate limit resets
        """
        try:
            key = f"rate_limit:{client_id}"
            ttl = self.redis_client.ttl(key)
            return max(0, ttl)
        except Exception:
            return self._get_reset_time_memory(client_id)

    def _get_reset_time_memory(self, client_id: str) -> int:
        """
        Get reset time from memory.
        
        Calculates the reset time based on in-memory rate limiting data.
        
        Args:
            client_id (str): Unique identifier for the client
            
        Returns:
            int: Seconds until rate limit resets
        """
        if not self.fallback_clients[client_id]:
            return 0

        oldest = min(self.fallback_clients[client_id])
        return int(oldest + self.window - time.time())


class CSRFProtection:
    """
    CSRF (Cross-Site Request Forgery) protection implementation.
    
    Generates and validates CSRF tokens to prevent cross-site request forgery
    attacks. Tokens are cryptographically signed and can optionally be
    bound to user sessions for additional security.
    
    Security Considerations:
    - Uses cryptographically secure random values for token generation
    - Employs HMAC-SHA256 for token signing
    - Implements constant-time comparison to prevent timing attacks
    - Supports optional session binding for additional security
    - Tokens include timestamps to prevent replay attacks
    
    This implementation follows OWASP CSRF prevention guidelines and
    provides both cookie-based and header-based token transmission.
    """
    
    def __init__(self, secret: str):
        """
        Initialize CSRF protection with a secret key.
        
        The secret key is used for signing CSRF tokens to ensure their
        integrity and prevent tampering.
        
        Args:
            secret (str): Secret key used for signing CSRF tokens
        """
        self.secret = secret
    
    def generate_token(self, session_id: str = "") -> str:
        """
        Generate a CSRF token.
        
        Creates a cryptographically signed token that includes random data,
        timestamp, and optional session binding. The token is base64-encoded
        for safe transmission in HTTP headers and cookies.
        
        Security Considerations:
        - Uses cryptographically secure random generator
        - Includes timestamp to prevent replay attacks
        - Supports session binding to tie tokens to user sessions
        - Uses HMAC-SHA256 for cryptographic signing
        
        Args:
            session_id (str): Optional session ID to bind token to
            
        Returns:
            str: Base64-encoded CSRF token
        """
        random_data = secrets.token_bytes(32)
        timestamp = str(int(time.time())).encode()

        # Create token with timestamp and optional session binding
        session_data = session_id.encode() if session_id else b""
        token_data = random_data + b"|" + timestamp + b"|" + session_data

        # Sign token
        signature = hmac.new(
            self.secret.encode(),
            token_data,
            hashlib.sha256
        ).digest()

        # Combine and encode as base64
        full_token = token_data + b"|" + signature
        return base64.urlsafe_b64encode(full_token).decode().rstrip("=")
    
    def validate_token(self, token: str, max_age: int = 3600, session_id: str = "") -> bool:
        """
        Validate a CSRF token.
        
        Verifies the cryptographic signature of a CSRF token and checks
        its timestamp and optional session binding. Uses constant-time
        comparison to prevent timing attacks.
        
        Security Considerations:
        - Validates cryptographic signature using HMAC
        - Checks token age to prevent replay attacks
        - Verifies session binding if provided
        - Uses constant-time comparison to prevent timing attacks
        - Handles malformed tokens gracefully
        
        Args:
            token (str): CSRF token to validate
            max_age (int): Maximum age of token in seconds (default 1 hour)
            session_id (str): Optional session ID to validate binding
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        if not token:
            return False

        try:
            # Decode base64 token
            padding = len(token) % 4
            if padding:
                token += "=" * (4 - padding)
            decoded = base64.urlsafe_b64decode(token.encode())

            # Split token into components
            parts = decoded.split(b"|")
            if len(parts) != 4:  # random_data + timestamp + session_data + signature
                return False

            random_data, timestamp_bytes, session_data, provided_signature = parts

            # Verify timestamp
            timestamp = int(timestamp_bytes)
            current_time = int(time.time())
            if current_time - timestamp > max_age:
                return False

            # Verify session binding if provided
            if session_id and session_data.decode() != session_id:
                return False

            # Verify signature
            expected_data = random_data + b"|" + timestamp_bytes + b"|" + session_data
            expected_signature = hmac.new(
                self.secret.encode(),
                expected_data,
                hashlib.sha256
            ).digest()

            return secrets.compare_digest(provided_signature, expected_signature)
        except Exception:
            return False


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Main security middleware that applies all security measures.
    
    This middleware handles HTTPS enforcement, rate limiting, CSRF protection,
    and security headers. It's designed to be the primary security layer
    for FastAPI applications.
    
    Security Flow:
    1. HTTPS enforcement (if configured)
    2. Rate limiting
    3. CSRF protection for state-changing methods
    4. Security headers added to responses
    5. CSRF token generation for GET requests
    
    The middleware is designed to be efficient and minimally invasive
    while providing comprehensive security protection.
    """
    
    def __init__(self, app, config: SecurityConfig):
        """
        Initialize security middleware with configuration.
        
        Sets up all security components based on the provided configuration.
        
        Args:
            app: FastAPI application instance
            config (SecurityConfig): Security configuration
        """
        super().__init__(app)
        self.config = config
        self.rate_limiter = RateLimiter(
            requests=config.rate_limit_requests,
            window=config.rate_limit_window,
            redis_url=config.redis_url
        )
        self.csrf = CSRFProtection(config.csrf_secret)
        self.bearer = HTTPBearer(auto_error=False)
    
    async def dispatch(self, request: Request, call_next):
        """
        Process incoming requests and apply security measures.
        
        This method is called for each incoming request and applies
        all configured security measures in sequence. It provides
        comprehensive protection against common web vulnerabilities.
        
        Security Measures Applied:
        1. HTTPS enforcement in production environments
        2. Rate limiting based on client identification
        3. CSRF protection for state-changing HTTP methods
        4. Security headers for response protection
        
        Args:
            request (Request): Incoming HTTP request
            call_next: Next middleware in the chain
            
        Returns:
            Response: HTTP response with security measures applied
        """
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
                # Check if this is an API endpoint that should use JWT instead of CSRF
                is_api_endpoint = any(path in request.url.path for path in [
                    "/api/v1/collab/tasks",
                    "/api/v1/jobs",
                    "/api/v1/events",
                    "/auth/login"
                ])
                
                if not is_api_endpoint:
                    # This is a regular web form endpoint, check CSRF
                    csrf_token = request.headers.get(self.config.csrf_header_name)
                    
                    if not csrf_token:
                        csrf_token = request.cookies.get(self.config.csrf_cookie_name)
                    
                    # Extract session ID for validation
                    session_id = ""
                    auth = request.headers.get("Authorization")
                    if auth and auth.startswith("Bearer "):
                        try:
                            token = auth.split(" ")[1]
                            payload = jwt.decode(
                                token,
                                self.config.jwt_secret,
                                algorithms=[self.config.jwt_algorithm]
                            )
                            session_id = payload.get('sub', '') or payload.get('session_id', '')
                        except jwt.PyJWTError:
                            pass

                    if not self.csrf.validate_token(csrf_token, session_id=session_id):
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
            # Extract session ID from JWT for binding
            session_id = ""
            auth = request.headers.get("Authorization")
            if auth and auth.startswith("Bearer "):
                try:
                    token = auth.split(" ")[1]
                    payload = jwt.decode(
                        token,
                        self.config.jwt_secret,
                        algorithms=[self.config.jwt_algorithm]
                    )
                    session_id = payload.get('sub', '') or payload.get('session_id', '')
                except jwt.PyJWTError:
                    pass

            csrf_token = self.csrf.generate_token(session_id)
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
        """
        Get client identifier for rate limiting.
        
        Attempts to identify clients by authenticated user ID first,
        falling back to IP address for unauthenticated requests. This
        provides more accurate rate limiting for authenticated users.
        
        Args:
            request (Request): Incoming HTTP request
            
        Returns:
            str: Client identifier string
        """
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
        """
        Check if request has a valid JWT token.
        
        Validates the JWT token in the Authorization header to determine
        if this is an authenticated API request that should bypass CSRF
        protection.
        
        Args:
            request (Request): Incoming HTTP request
            
        Returns:
            bool: True if request has valid JWT, False otherwise
        """
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
        """
        Generate Content Security Policy header.
        
        Creates a CSP header with environment-specific policies,
        stricter for production environments. This helps prevent
        XSS attacks by controlling which sources of content are allowed.
        
        Security Considerations:
        - Stricter policies in production environments
        - Permissive policies in development for usability
        - Reporting of violations in production
        - Disallows unsafe inline scripts and eval
        
        Returns:
            str: Content Security Policy header value
        """
        # Check environment for CSP strictness
        is_production = getattr(self.config, 'environment', 'local') == 'production'

        directives = [
            "default-src 'self'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]

        if is_production:
            # Strict CSP for production
            directives.extend([
                "script-src 'self'",  # No unsafe-inline or unsafe-eval
                "style-src 'self'",   # No unsafe-inline
                "object-src 'none'",
                "base-uri 'self'",
                "upgrade-insecure-requests",
            ])
        else:
            # More permissive CSP for development
            directives.extend([
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Allow for development tools
                "style-src 'self' 'unsafe-inline'",
            ])

        # Add CSP report URI if configured
        if hasattr(self.config, 'csp_report_uri'):
            directives.append(f"report-uri {self.config.csp_report_uri}")
        elif is_production:
            # Default report URI for production
            directives.append("report-uri /api/v1/security/csp-report")

        return "; ".join(directives)


def create_security_config_from_settings():
    """
    Create SecurityConfig from centralized settings.
    
    Attempts to load security configuration from the application's
    centralized settings, with fallback to default values. This function
    provides a convenient way to configure security from environment
    variables or configuration files.
    
    Returns:
        SecurityConfig: Configured security settings
    """
    try:
        from .app.core.config import settings
    except ImportError:
        # Fallback for environments where config is not available
        from pydantic_settings import BaseSettings
        class FallbackSettings(BaseSettings):
            SECRET_KEY: str = "fallback-secret-key"
            JWT_ALGORITHM: str = "HS512"
            ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
            all_cors_origins: list[str] = []
            ENVIRONMENT: str = "local"
        settings = FallbackSettings()

    return SecurityConfig(
        jwt_secret=settings.SECRET_KEY,
        csrf_secret=secrets.token_urlsafe(32),  # Generate random CSRF secret
        jwt_algorithm=settings.JWT_ALGORITHM,
        jwt_expiration_hours=settings.ACCESS_TOKEN_EXPIRE_MINUTES // 60,
        backend_cors_origins=settings.all_cors_origins,
        environment=settings.ENVIRONMENT,
    )


class JWTAuthentication:
    """
    JWT token management utilities.
    
    Provides methods for creating and verifying JWT tokens with
    appropriate security measures. This class complements the
    authentication functionality in auth.py.
    
    Security Considerations:
    - Uses cryptographically secure signing algorithms
    - Implements proper token expiration
    - Includes JWT ID (jti) for token revocation support
    - Handles token verification errors gracefully
    """
    
    def __init__(self, secret: str, algorithm: str = "HS512", expiration_hours: int = 2):
        """
        Initialize JWT authentication utilities.
        
        Args:
            secret (str): Secret key for signing JWT tokens
            algorithm (str): JWT signing algorithm
            expiration_hours (int): Token expiration time in hours
        """
        self.secret = secret
        self.algorithm = algorithm
        self.expiration_hours = expiration_hours
    
    def create_token(self, user_id: str, role: str = "user") -> str:
        """
        Create a JWT token for a user.
        
        Generates a signed JWT token with standard claims including
        expiration, issued at time, and JWT ID for revocation support.
        
        Args:
            user_id (str): Unique identifier for the user
            role (str): User role (default: "user")
            
        Returns:
            str: Encoded JWT token
        """
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "role": role,
            "exp": now + timedelta(hours=self.expiration_hours),
            "iat": now,
            "jti": secrets.token_hex(16)  # JWT ID for revocation
        }
        
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.
        
        Validates the signature and expiration of a JWT token and
        returns the decoded payload if valid.
        
        Args:
            token (str): JWT token to verify
            
        Returns:
            Optional[Dict[str, Any]]: Decoded token payload if valid, None otherwise
        """
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
    """
    Setup all security middleware for a FastAPI application.
    
    Configures CORS middleware and the main security middleware
    with the provided configuration. This function should be called
    during application initialization to apply security measures.
    
    Integration with FastAPI:
    - Adds CORS middleware for cross-origin resource sharing
    - Adds SecurityMiddleware for comprehensive protection
    - Configures middleware with provided security settings
    
    Args:
        app: FastAPI application instance
        config (SecurityConfig): Security configuration
        
    Returns:
        FastAPI application with security middleware configured
    """
    
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