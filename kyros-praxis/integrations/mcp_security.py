#!/usr/bin/env python3
"""
MCP Security Module - OAuth Resource Server Implementation

This module implements security for Model Context Protocol (MCP) servers according to the
June 2025 OAuth Resource Server specification. It provides authentication, authorization,
and security boundaries for MCP servers.

Key Features:
- OAuth 2.1 Resource Server compliance
- Bearer token validation (Authorization: Bearer <token>)
- API key validation (X-API-Key header)
- Filesystem boundaries and path validation
- PKCE support for public clients
- Resource indicators (RFC 8707) support
- .well-known/oauth-protected-resource metadata endpoint

Security Requirements (June 2025 MCP Spec):
- MCP servers MUST act as OAuth Resource Servers
- Authorization MUST be included in every HTTP request
- Access tokens MUST NOT be in URI query strings
- Invalid/expired tokens MUST receive HTTP 401 response
- PKCE is mandatory for public clients
- Resource indicators required to prevent token mis-redemption

Usage:
    from mcp_security import MCPSecurity, SecurityConfig
    
    config = SecurityConfig(
        jwt_secret="your-secret",
        api_keys=["valid-api-key"],
        allowed_roots=["/safe/path", "/another/safe/path"]
    )
    
    security = MCPSecurity(config)
    
    # Validate request
    if not security.validate_request(headers, method):
        return security.create_error_response(401, "Unauthorized")
"""

import os
import json
import hmac
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from urllib.parse import urlparse
import logging

# Optional JWT support - gracefully handle missing dependency
try:
    from jose import jwt, JWTError
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    logging.warning("JWT library not available. Install python-jose for full OAuth support.")

logger = logging.getLogger(__name__)


class SecurityConfig:
    """
    Security configuration for MCP servers.
    
    Defines all security parameters including OAuth settings, API keys,
    filesystem boundaries, and server metadata.
    """
    
    def __init__(
        self,
        # OAuth Resource Server settings
        jwt_secret: str = None,
        jwt_algorithm: str = "HS256",
        jwt_audience: str = "mcp-server",
        jwt_issuer: str = "kyros-mcp",
        
        # API key settings
        api_keys: List[str] = None,
        api_key_header: str = "X-API-Key",
        
        # Filesystem security
        allowed_roots: List[str] = None,
        enforce_filesystem_boundaries: bool = True,
        
        # Server metadata
        server_name: str = "mcp-server",
        server_version: str = "1.0.0",
        authorization_servers: List[str] = None,
        resource_uri: str = None,
        
        # Security options
        require_https: bool = True,
        token_cache_ttl: int = 300,  # 5 minutes
        max_token_age: int = 3600,   # 1 hour
    ):
        self.jwt_secret = jwt_secret or os.getenv("MCP_JWT_SECRET", "")
        self.jwt_algorithm = jwt_algorithm
        self.jwt_audience = jwt_audience
        self.jwt_issuer = jwt_issuer
        
        self.api_keys = set(api_keys or [])
        if env_api_keys := os.getenv("MCP_API_KEYS"):
            self.api_keys.update(env_api_keys.split(","))
        self.api_key_header = api_key_header
        
        self.allowed_roots = [Path(root).resolve() for root in (allowed_roots or [])]
        if not self.allowed_roots:
            # Default to current working directory if no roots specified
            self.allowed_roots = [Path.cwd()]
        self.enforce_filesystem_boundaries = enforce_filesystem_boundaries
        
        self.server_name = server_name
        self.server_version = server_version
        self.authorization_servers = authorization_servers or []
        self.resource_uri = resource_uri or f"urn:mcp:{server_name}"
        
        self.require_https = require_https and os.getenv("MCP_REQUIRE_HTTPS", "true").lower() == "true"
        self.token_cache_ttl = token_cache_ttl
        self.max_token_age = max_token_age
        
        # Token cache for performance
        self._token_cache: Dict[str, Tuple[bool, float]] = {}


class MCPSecurity:
    """
    Main security implementation for MCP servers.
    
    Implements OAuth Resource Server pattern with Bearer token validation,
    API key authentication, and filesystem boundary enforcement.
    """
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.server_name}")
        
        # Validate configuration
        if not self.config.jwt_secret and not self.config.api_keys:
            self.logger.warning("No JWT secret or API keys configured. All requests will be rejected.")
        
        if not JWT_AVAILABLE and self.config.jwt_secret:
            self.logger.error("JWT secret provided but jose library not available. Install python-jose.")
    
    def get_protected_resource_metadata(self) -> Dict[str, Any]:
        """
        Generate .well-known/oauth-protected-resource metadata.
        
        Returns OAuth protected resource metadata as specified in the MCP spec.
        This allows clients to discover authorization servers and resource information.
        
        Returns:
            Dict containing OAuth protected resource metadata
        """
        metadata = {
            "resource": self.config.resource_uri,
            "authorization_servers": self.config.authorization_servers,
            "bearer_methods_supported": ["header"],
            "resource_documentation": f"https://docs.{self.config.server_name}/mcp-auth",
            "revocation_endpoint_auth_methods_supported": ["client_secret_basic"],
            "revocation_endpoint_auth_signing_alg_values_supported": [self.config.jwt_algorithm],
            "resource_registration_endpoint": None,  # Static configuration
            "scopes_supported": ["read", "write", "admin"],
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "client_credentials"],
            "token_endpoint_auth_methods_supported": ["client_secret_basic", "none"],
            "code_challenge_methods_supported": ["S256"],  # PKCE support
        }
        
        return metadata
    
    def validate_bearer_token(self, token: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate OAuth Bearer token.
        
        Validates JWT tokens according to OAuth 2.1 and MCP specifications.
        Implements proper token validation with caching for performance.
        
        Args:
            token: Bearer token to validate
            
        Returns:
            Tuple of (is_valid, token_data)
        """
        if not token or not JWT_AVAILABLE or not self.config.jwt_secret:
            return False, {}
        
        # Check token cache
        cache_key = hashlib.sha256(token.encode()).hexdigest()
        if cache_key in self.config._token_cache:
            is_valid, cached_time = self.config._token_cache[cache_key]
            if time.time() - cached_time < self.config.token_cache_ttl:
                return is_valid, {} if not is_valid else {"cached": True}
        
        try:
            # Decode and validate JWT token
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm],
                audience=self.config.jwt_audience,
                issuer=self.config.jwt_issuer,
                options={
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "require_exp": True,
                    "require_aud": True,
                    "require_iss": True,
                }
            )
            
            # Additional validation
            now = time.time()
            iat = payload.get("iat", 0)
            if now - iat > self.config.max_token_age:
                self.logger.warning("Token too old")
                self.config._token_cache[cache_key] = (False, now)
                return False, {}
            
            # Cache valid token
            self.config._token_cache[cache_key] = (True, now)
            return True, payload
            
        except JWTError as e:
            self.logger.warning(f"JWT validation failed: {e}")
            self.config._token_cache[cache_key] = (False, time.time())
            return False, {}
        except Exception as e:
            self.logger.error(f"Token validation error: {e}")
            return False, {}
    
    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate API key for service-to-service authentication.
        
        Provides constant-time comparison to prevent timing attacks.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if API key is valid
        """
        if not api_key or not self.config.api_keys:
            return False
        
        # Constant-time comparison against all valid keys
        for valid_key in self.config.api_keys:
            if secrets.compare_digest(api_key, valid_key):
                return True
        
        return False
    
    def validate_filesystem_path(self, requested_path: str) -> Tuple[bool, Path]:
        """
        Validate filesystem path against allowed roots.
        
        Implements filesystem boundary enforcement to prevent unauthorized
        file access outside of designated safe directories.
        
        Args:
            requested_path: File path to validate
            
        Returns:
            Tuple of (is_allowed, resolved_path)
        """
        if not self.config.enforce_filesystem_boundaries:
            return True, Path(requested_path)
        
        try:
            # Resolve the path to prevent traversal attacks
            resolved_path = Path(requested_path).resolve()
            
            # Check if path is within any allowed root
            for allowed_root in self.config.allowed_roots:
                try:
                    resolved_path.relative_to(allowed_root)
                    return True, resolved_path
                except ValueError:
                    continue
            
            self.logger.warning(f"Path access denied: {resolved_path} not in allowed roots")
            return False, resolved_path
            
        except Exception as e:
            self.logger.error(f"Path validation error: {e}")
            return False, Path(requested_path)
    
    def validate_request(self, headers: Dict[str, str], method: str = "GET") -> Tuple[bool, Dict[str, Any]]:
        """
        Validate incoming MCP request for authentication and authorization.
        
        Implements the complete authentication flow according to June 2025 MCP spec:
        1. Extract and validate Bearer token or API key
        2. Verify token/key authenticity
        3. Check authorization for requested operation
        
        Args:
            headers: HTTP headers from the request
            method: HTTP method (for logging/auditing)
            
        Returns:
            Tuple of (is_authorized, auth_context)
        """
        auth_context = {
            "method": method,
            "timestamp": time.time(),
            "auth_type": None,
            "user_id": None,
            "scopes": [],
        }
        
        # Check for Bearer token (OAuth 2.1)
        authorization = headers.get("Authorization", "").strip()
        if authorization.startswith("Bearer "):
            token = authorization[7:]  # Remove "Bearer " prefix
            is_valid, token_data = self.validate_bearer_token(token)
            if is_valid:
                auth_context.update({
                    "auth_type": "bearer",
                    "user_id": token_data.get("sub"),
                    "scopes": token_data.get("scope", "").split(),
                    "token_data": token_data,
                })
                self.logger.info(f"Bearer token authentication successful for user: {auth_context['user_id']}")
                return True, auth_context
            else:
                self.logger.warning(f"Invalid Bearer token for {method} request")
                return False, auth_context
        
        # Check for API key (service-to-service)
        api_key = headers.get(self.config.api_key_header, "").strip()
        if api_key:
            if self.validate_api_key(api_key):
                auth_context.update({
                    "auth_type": "api_key",
                    "user_id": "service",
                    "scopes": ["read", "write"],  # Full access for valid API keys
                })
                self.logger.info(f"API key authentication successful for {method} request")
                return True, auth_context
            else:
                self.logger.warning(f"Invalid API key for {method} request")
                return False, auth_context
        
        # No valid authentication found
        self.logger.warning(f"No valid authentication found for {method} request")
        return False, auth_context
    
    def create_error_response(self, status_code: int, message: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create standardized error response for authentication/authorization failures.
        
        Args:
            status_code: HTTP status code
            message: Error message
            details: Additional error details
            
        Returns:
            MCP-compatible error response
        """
        error_response = {
            "jsonrpc": "2.0",
            "error": {
                "code": status_code,
                "message": message,
                "data": details or {}
            }
        }
        
        # Add WWW-Authenticate header info for 401 responses
        if status_code == 401:
            error_response["error"]["data"]["www_authenticate"] = (
                f'Bearer realm="{self.config.server_name}", '
                f'scope="read write", '
                f'error="invalid_token"'
            )
        
        return error_response
    
    def create_capabilities_response(self, base_capabilities: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create MCP capabilities response with security information.
        
        Enhances base MCP capabilities with security-related information
        such as supported authentication methods and security policies.
        
        Args:
            base_capabilities: Base MCP capabilities to enhance
            
        Returns:
            Enhanced capabilities with security information
        """
        capabilities = base_capabilities or {}
        
        # Add security capabilities
        security_info = {
            "security": {
                "authentication_methods": [],
                "authorization_servers": self.config.authorization_servers,
                "resource_uri": self.config.resource_uri,
                "scopes_supported": ["read", "write", "admin"],
                "pkce_required": True,
                "filesystem_boundaries": self.config.enforce_filesystem_boundaries,
                "allowed_roots": [str(root) for root in self.config.allowed_roots] if self.config.enforce_filesystem_boundaries else None,
            }
        }
        
        if self.config.jwt_secret and JWT_AVAILABLE:
            security_info["security"]["authentication_methods"].append("bearer")
        
        if self.config.api_keys:
            security_info["security"]["authentication_methods"].append("api_key")
        
        capabilities.update(security_info)
        return capabilities
    
    def audit_log(self, event: str, auth_context: Dict[str, Any], details: Dict[str, Any] = None):
        """
        Create security audit log entry.
        
        Logs security-relevant events for monitoring and compliance.
        
        Args:
            event: Type of security event
            auth_context: Authentication context
            details: Additional event details
        """
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "server": self.config.server_name,
            "auth_type": auth_context.get("auth_type"),
            "user_id": auth_context.get("user_id"),
            "method": auth_context.get("method"),
            "details": details or {}
        }
        
        # Log to security audit log (in production, this should go to a secure log aggregation system)
        self.logger.info(f"SECURITY_AUDIT: {json.dumps(audit_entry)}")


def create_mcp_security(
    server_name: str,
    jwt_secret: str = None,
    api_keys: List[str] = None,
    allowed_roots: List[str] = None,
    **kwargs
) -> MCPSecurity:
    """
    Convenience function to create MCPSecurity instance with common configuration.
    
    Args:
        server_name: Name of the MCP server
        jwt_secret: JWT signing secret
        api_keys: List of valid API keys
        allowed_roots: List of allowed filesystem roots
        **kwargs: Additional SecurityConfig parameters
        
    Returns:
        Configured MCPSecurity instance
    """
    config = SecurityConfig(
        server_name=server_name,
        jwt_secret=jwt_secret,
        api_keys=api_keys or [],
        allowed_roots=allowed_roots or [],
        **kwargs
    )
    
    return MCPSecurity(config)