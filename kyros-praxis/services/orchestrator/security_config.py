"""
Security configuration management for Kyros Orchestrator.

This module provides centralized security configuration management with
environment-specific settings for development, staging, and production
deployments. It ensures security best practices are applied consistently.

SECURITY CONFIGURATION FEATURES:
-------------------------------
1. Environment-Specific Settings:
   - Development: Relaxed settings for local development
   - Production: Strict security policies for production
   - Testing: Isolated settings for test environments

2. Rate Limiting Configuration:
   - Adaptive rate limits based on environment
   - Burst protection for API endpoints
   - Redis-backed distributed rate limiting

3. JWT Security Settings:
   - Environment-appropriate token lifetimes
   - Secure algorithm selection
   - Key rotation support

4. CSRF Protection Settings:
   - Environment-specific CSRF policies
   - Secure cookie configuration
   - Token validation settings

5. TLS/HTTPS Configuration:
   - Production HTTPS enforcement
   - Certificate validation settings
   - Secure header configuration
"""

import os
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass


class Environment(str, Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class SecurityProfile:
    """Security configuration profile for different environments."""
    
    # Rate limiting settings
    rate_limit_requests: int
    rate_limit_window: int
    rate_limit_burst: int
    
    # JWT settings
    jwt_lifetime_minutes: int
    jwt_algorithm: str
    require_strong_secrets: bool
    
    # CSRF settings
    csrf_enabled: bool
    csrf_strict_referer_check: bool
    
    # TLS/HTTPS settings
    force_https: bool
    hsts_enabled: bool
    secure_cookies: bool
    
    # Security headers
    csp_enabled: bool
    x_frame_options: str
    x_content_type_options: bool
    
    # Audit and monitoring
    audit_all_requests: bool
    failed_auth_lockout_enabled: bool
    suspicious_activity_detection: bool


class SecurityConfigManager:
    """Manages security configuration across environments."""
    
    # Security profiles for different environments
    PROFILES: Dict[Environment, SecurityProfile] = {
        Environment.DEVELOPMENT: SecurityProfile(
            rate_limit_requests=1000,
            rate_limit_window=900,
            rate_limit_burst=100,
            jwt_lifetime_minutes=120,  # 2 hours for development
            jwt_algorithm="HS256",
            require_strong_secrets=False,
            csrf_enabled=True,
            csrf_strict_referer_check=False,
            force_https=False,
            hsts_enabled=False,
            secure_cookies=False,
            csp_enabled=False,
            x_frame_options="SAMEORIGIN",
            x_content_type_options=True,
            audit_all_requests=False,
            failed_auth_lockout_enabled=False,
            suspicious_activity_detection=False
        ),
        
        Environment.STAGING: SecurityProfile(
            rate_limit_requests=200,
            rate_limit_window=900,
            rate_limit_burst=50,
            jwt_lifetime_minutes=60,  # 1 hour for staging
            jwt_algorithm="HS256",
            require_strong_secrets=True,
            csrf_enabled=True,
            csrf_strict_referer_check=True,
            force_https=True,
            hsts_enabled=True,
            secure_cookies=True,
            csp_enabled=True,
            x_frame_options="DENY",
            x_content_type_options=True,
            audit_all_requests=True,
            failed_auth_lockout_enabled=True,
            suspicious_activity_detection=True
        ),
        
        Environment.PRODUCTION: SecurityProfile(
            rate_limit_requests=100,
            rate_limit_window=900,
            rate_limit_burst=20,
            jwt_lifetime_minutes=30,  # 30 minutes for production
            jwt_algorithm="RS256",  # More secure for production
            require_strong_secrets=True,
            csrf_enabled=True,
            csrf_strict_referer_check=True,
            force_https=True,
            hsts_enabled=True,
            secure_cookies=True,
            csp_enabled=True,
            x_frame_options="DENY",
            x_content_type_options=True,
            audit_all_requests=True,
            failed_auth_lockout_enabled=True,
            suspicious_activity_detection=True
        ),
        
        Environment.TESTING: SecurityProfile(
            rate_limit_requests=10000,
            rate_limit_window=900,
            rate_limit_burst=1000,
            jwt_lifetime_minutes=15,  # Short for tests
            jwt_algorithm="HS256",
            require_strong_secrets=False,
            csrf_enabled=False,  # Disabled for easier testing
            csrf_strict_referer_check=False,
            force_https=False,
            hsts_enabled=False,
            secure_cookies=False,
            csp_enabled=False,
            x_frame_options="SAMEORIGIN",
            x_content_type_options=True,
            audit_all_requests=False,
            failed_auth_lockout_enabled=False,
            suspicious_activity_detection=False
        )
    }
    
    def __init__(self, environment: Optional[Environment] = None):
        """Initialize security configuration manager."""
        self.environment = environment or self._detect_environment()
        self.profile = self.PROFILES[self.environment]
    
    @staticmethod
    def _detect_environment() -> Environment:
        """Detect environment from environment variables."""
        env_name = os.getenv("ENVIRONMENT", "development").lower()
        
        # Map common environment names
        env_mapping = {
            "dev": Environment.DEVELOPMENT,
            "development": Environment.DEVELOPMENT,
            "local": Environment.DEVELOPMENT,
            "stage": Environment.STAGING,
            "staging": Environment.STAGING,
            "prod": Environment.PRODUCTION,
            "production": Environment.PRODUCTION,
            "test": Environment.TESTING,
            "testing": Environment.TESTING,
        }
        
        return env_mapping.get(env_name, Environment.DEVELOPMENT)
    
    def get_rate_limit_config(self) -> Dict[str, int]:
        """Get rate limiting configuration for current environment."""
        return {
            "requests": self.profile.rate_limit_requests,
            "window": self.profile.rate_limit_window,
            "burst": self.profile.rate_limit_burst
        }
    
    def get_jwt_config(self) -> Dict[str, Any]:
        """Get JWT configuration for current environment."""
        return {
            "lifetime_minutes": self.profile.jwt_lifetime_minutes,
            "algorithm": self.profile.jwt_algorithm,
            "require_strong_secrets": self.profile.require_strong_secrets
        }
    
    def get_csrf_config(self) -> Dict[str, Any]:
        """Get CSRF configuration for current environment."""
        return {
            "enabled": self.profile.csrf_enabled,
            "strict_referer_check": self.profile.csrf_strict_referer_check
        }
    
    def get_tls_config(self) -> Dict[str, Any]:
        """Get TLS/HTTPS configuration for current environment."""
        return {
            "force_https": self.profile.force_https,
            "hsts_enabled": self.profile.hsts_enabled,
            "secure_cookies": self.profile.secure_cookies
        }
    
    def get_security_headers(self) -> Dict[str, Any]:
        """Get security headers configuration for current environment."""
        headers = {
            "X-Content-Type-Options": "nosniff" if self.profile.x_content_type_options else None,
            "X-Frame-Options": self.profile.x_frame_options,
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "X-XSS-Protection": "1; mode=block",
        }
        
        if self.profile.hsts_enabled:
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        if self.profile.csp_enabled:
            headers["Content-Security-Policy"] = self._generate_csp_header()
        
        # Filter out None values
        return {k: v for k, v in headers.items() if v is not None}
    
    def _generate_csp_header(self) -> str:
        """Generate Content Security Policy header for current environment."""
        if self.environment == Environment.PRODUCTION:
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "font-src 'self'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        else:
            # More relaxed CSP for development/staging
            return (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' ws: wss:; "
                "object-src 'none'"
            )
    
    def get_audit_config(self) -> Dict[str, bool]:
        """Get audit configuration for current environment."""
        return {
            "audit_all_requests": self.profile.audit_all_requests,
            "failed_auth_lockout_enabled": self.profile.failed_auth_lockout_enabled,
            "suspicious_activity_detection": self.profile.suspicious_activity_detection
        }
    
    def validate_secret_strength(self, secret: str) -> bool:
        """Validate if a secret meets security requirements for current environment."""
        if not self.profile.require_strong_secrets:
            return True
        
        # Strong secret requirements
        return (
            len(secret) >= 32 and
            any(c.isupper() for c in secret) and
            any(c.islower() for c in secret) and
            any(c.isdigit() for c in secret) and
            any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in secret)
        )
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT


# Global security config instance
security_config = SecurityConfigManager()


def get_security_config() -> SecurityConfigManager:
    """Get the global security configuration manager."""
    return security_config


def configure_security_for_environment(environment: Environment) -> SecurityConfigManager:
    """Configure security for a specific environment."""
    return SecurityConfigManager(environment)