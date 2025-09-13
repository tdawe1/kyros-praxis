"""
Configuration management using Pydantic Settings.
Centralized configuration for the orchestrator service.
"""
import secrets
import warnings
from typing import Annotated, Any, Literal, Optional

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


def parse_cors(v: Any) -> list[str] | str:
    """Parse CORS origins from string or list."""
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        # Use top level .env file (two levels above ./services/orchestrator/)
        env_file="../../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Kyros Praxis"
    VERSION: str = "0.1.0"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120  # 2 hours (reduced from 8 days)
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    JWT_ALGORITHM: str = "HS512"  # Changed from HS256 to HS512 for stronger security
    JWKS_URL: Optional[str] = None
    JWT_ISSUER: str = "kyros-praxis"
    JWT_AUDIENCE: str = "kyros-app"
    
    # Environment
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    
    # Frontend
    FRONTEND_HOST: str = "http://localhost:3001"
    
    # CORS
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        """Get all CORS origins."""
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "kyros"
    
    # Legacy DB vars support
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_NAME: Optional[str] = None
    
    @model_validator(mode="after")
    def _use_legacy_db_vars(self) -> Self:
        """Use legacy DB variables if new ones are not set."""
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
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        """Build SQLAlchemy database URI."""
        return PostgresDsn.build(
            scheme="postgresql+psycopg2",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_URL: Optional[str] = None
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_url(self) -> str:
        """Get Redis URL."""
        if self.REDIS_URL:
            return self.REDIS_URL
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"
    
    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    
    # Email
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        """Set default email from name."""
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        """Check if email is enabled."""
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)
    
    # First Superuser (for development)
    FIRST_SUPERUSER: Optional[EmailStr] = None
    FIRST_SUPERUSER_PASSWORD: Optional[str] = None
    
    # Feature Flags
    ENABLE_LOCAL_PASSWORD_AUTH: bool = False
    ENABLE_SEED: bool = False
    ENABLE_ADMINER: bool = False
    
    # Monitoring
    SENTRY_DSN: Optional[HttpUrl] = None
    
    # OpenTelemetry
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None
    OTEL_SERVICE_NAME: str = "kyros-praxis-orchestrator"
    
    def _check_default_secret(self, var_name: str, value: Optional[str]) -> None:
        """Check for default secrets and warn/error."""
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
        """Enforce non-default secrets in non-local environments."""
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        if self.FIRST_SUPERUSER_PASSWORD:
            self._check_default_secret(
                "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
            )
        return self


# Create global settings instance
settings = Settings()