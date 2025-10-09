"""
Configuration Management Using Pydantic Settings

This module provides centralized configuration management for the Kyros Orchestrator service
using Pydantic Settings. It defines the Settings class that loads configuration from
environment variables and .env files, with sensible defaults for local development.

The configuration includes:
- API configuration (version, project name)
- Security settings (secrets, JWT, CORS)
- Database connection settings
- Redis and Qdrant service configuration
- Email service settings
- Feature flags
- Monitoring and logging configuration
- Environment-specific settings

The Settings class uses Pydantic's model validation to ensure configuration correctness
and provides computed properties for derived configuration values.
"""

import secrets
import warnings
from typing import Annotated, Any, Literal, Optional

from pydantic import (
    AnyUrl,
    BeforeValidator,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


def parse_cors(v: Any) -> list[str] | str:
    """
    Parse CORS origins from string or list.
    
    This utility function parses CORS origins from either a comma-separated
    string or a list, returning a standardized list format for further processing.
    
    Args:
        v (Any): Input value to parse (string or list)
        
    Returns:
        Union[list[str], str]: Parsed CORS origins as list or original value
        
    Raises:
        ValueError: If input cannot be parsed
    """
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    """
    Application settings.
    
    This class defines all configuration settings for the Kyros Orchestrator service.
    It loads settings from environment variables and .env files, with validation
    and computed properties for derived values.
    
    The configuration is organized into logical sections:
    - API Configuration: Service identification and versioning
    - Security: Secrets, JWT, CORS, and authentication settings
    - Environment: Deployment environment configuration
    - Frontend: Frontend service configuration
    - CORS: Cross-Origin Resource Sharing settings
    - Database: Database connection settings
    - Redis: Redis service configuration
    - Qdrant: Qdrant vector database configuration
    - Email: Email service settings
    - Users: First superuser account configuration
    - Features: Feature flag settings
    - Monitoring: Monitoring and observability configuration
    - Logging: Logging configuration
    - Orchestrator: Orchestrator-specific settings
    """
    
    model_config = SettingsConfigDict(
        # Use orchestrator .env file
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )
    
    # API Configuration
    # Service identification and versioning
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Kyros Praxis"
    VERSION: str = "0.1.0"
    
    # Security
    # Cryptographic secrets and JWT configuration
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120  # 2 hours (reduced from 8 days)
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    JWT_ALGORITHM: str = "HS512"  # Changed from HS256 to HS512 for stronger security
    JWKS_URL: Optional[str] = None
    JWT_ISSUER: str = "kyros-praxis"
    JWT_AUDIENCE: str = "kyros-app"
    
    # Environment
    # Deployment environment configuration
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    
    # Frontend
    # Frontend service configuration for CORS and redirects
    FRONTEND_HOST: str = "http://localhost:3001"
    
    # CORS
    # Cross-Origin Resource Sharing configuration
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        """
        Get all CORS origins.
        
        This computed property combines the configured backend CORS origins
        with the frontend host to create a complete list of allowed origins
        for CORS headers. It ensures the frontend host is always included
        in the CORS configuration.
        
        Returns:
            list[str]: Combined list of all allowed CORS origins
        """
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]
    
    # Database
    # PostgreSQL database connection configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "kyros"
    
    # Legacy DB vars support
    # Backward compatibility for older environment variable names
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_NAME: Optional[str] = None
    
    @model_validator(mode="after")
    def _use_legacy_db_vars(self) -> Self:
        """
        Use legacy DB variables if new ones are not set.
        
        This model validator provides backward compatibility by allowing
        older environment variable names (DB_*) to be used when the newer
        POSTGRES_* variables are not set. This facilitates gradual migration
        from older configuration schemes.
        
        Returns:
            Self: Updated settings instance with legacy variables applied
        """
        if self.DB_HOST and not self.POSTGRES_SERVER:
            self.POSTGRES_SERVER = self.DB_HOST
        if self.DB_PORT and not self.POSTGRES_PORT:
            self.POSTGRES_PORT = self.DB_PORT
        if self.DB_USER and not self.POSTGRES_USER:
            self.POSTGRES_USER = self.DB_USER
        if self.DB_PASSWORD and not self.POSTGRES_PASSWORD:
            self.POSTGRES_PASSWORD = self.DB_PASSWORD
        if self.DB_NAME and not self.POSTGRES_DB:
            self.POSTGRES_DB = self.DB_NAME
        return self
    
    # Direct database URL override (for alternative databases like SQLite)
    DATABASE_URL: Optional[str] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn | str:
        """
        Build SQLAlchemy database URI.
        
        This computed property constructs the database connection URI for
        SQLAlchemy. It prioritizes a direct DATABASE_URL if provided (useful
        for SQLite or other databases), otherwise builds a PostgreSQL URI
        from the individual connection parameters.
        
        Returns:
            Union[PostgresDsn, str]: Database connection URI
        """
        # Use DATABASE_URL if provided (for SQLite)
        if self.DATABASE_URL:
            return self.DATABASE_URL

        # Otherwise build PostgreSQL URI
        return PostgresDsn.build(
            scheme="postgresql+psycopg2",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )
    
    # Redis
    # Redis service configuration for caching and session storage
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_URL: Optional[str] = None
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_url(self) -> str:
        """
        Get Redis URL.
        
        This computed property constructs the Redis connection URL from
        individual configuration parameters. It prioritizes a directly
        configured REDIS_URL, otherwise builds the URL from host, port,
        and password components. Properly handles password authentication
        when a password is provided.
        
        Returns:
            str: Redis connection URL
        """
        if self.REDIS_URL:
            return self.REDIS_URL
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"
    
    # Qdrant
    # Qdrant vector database configuration for similarity search and embeddings
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    
    # Email
    # SMTP email service configuration for sending notifications
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        """
        Set default email from name.
        
        This model validator ensures that the email sender name is set
        to the project name if not explicitly configured. This provides
        a sensible default for email notifications while allowing
        customization when needed.
        
        Returns:
            Self: Updated settings instance with default email name set
        """
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        """
        Check if email is enabled.
        
        This computed property determines whether the email service is
        properly configured and enabled by checking for the presence
        of required configuration values (SMTP host and sender email).
        
        Returns:
            bool: True if email service is enabled, False otherwise
        """
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)
    
    # First Superuser (for development)
    # Development superuser account configuration for initial setup
    FIRST_SUPERUSER: Optional[str] = None
    FIRST_SUPERUSER_PASSWORD: Optional[str] = None
    
    # Feature Flags
    # Toggle switches for optional service features
    ENABLE_LOCAL_PASSWORD_AUTH: bool = False
    ENABLE_SEED: bool = False
    ENABLE_ADMINER: bool = False
    
    # Monitoring
    # Error tracking and performance monitoring configuration
    SENTRY_DSN: Optional[HttpUrl] = None
    
    # OpenTelemetry
    # Distributed tracing and metrics collection configuration
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None
    OTEL_SERVICE_NAME: str = "kyros-praxis-orchestrator"

    # Logging
    # Application logging configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None

    # Orchestrator ID for log file naming
    # Unique identifier for this orchestrator instance
    ORCH_ID: str = "o-glm"
    
    # Rate Limiting Configuration
    # Rate limiting settings for security and performance
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 900  # 15 minutes
    RATE_LIMIT_BURST: int = 0
    
    # Production-specific rate limiting
    PRODUCTION_RATE_LIMIT_REQUESTS: int = 1000
    PRODUCTION_RATE_LIMIT_WINDOW: int = 3600  # 1 hour
    PRODUCTION_RATE_LIMIT_BURST: int = 50
    
    def _check_default_secret(self, var_name: str, value: Optional[str]) -> None:
        """
        Check for default secrets and warn/error.
        
        This internal method validates that sensitive configuration values
        are not set to default/placeholder values that would compromise security.
        In local environments, it issues warnings; in other environments,
        it raises exceptions to prevent deployment with insecure defaults.
        
        Args:
            var_name (str): Name of the configuration variable being checked
            value (Optional[str]): Value of the configuration variable
            
        Raises:
            ValueError: If default secret is used in non-local environment
        """
        if value in ["changethis", "your_secret_key_here", "your-secret-key-here"]:
            message = (
                f'The value of {var_name} is "{value}", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)
    
    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        """
        Enforce non-default secrets in non-local environments.
        
        This model validator ensures that critical security secrets
        (SECRET_KEY, database password, superuser password) are not
        set to insecure default values in staging or production
        environments. It uses the _check_default_secret method to
        perform the actual validation.
        
        Returns:
            Self: Updated settings instance after validation
            
        Raises:
            ValueError: If default secrets are used in non-local environments
        """
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        if self.FIRST_SUPERUSER_PASSWORD:
            self._check_default_secret(
                "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
            )
        return self


# Create global settings instance
# This singleton instance is imported and used throughout the application
settings = Settings()
