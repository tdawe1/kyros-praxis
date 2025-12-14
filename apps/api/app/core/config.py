from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

    # LLM / CrewAI configuration
    OPENAI_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1")
    
    MODEL_PROVIDER: str = Field(default="openrouter")
    MODEL_NAME: str = Field(default="gpt-4o-mini")

    # CORS / Console integration
    CORS_ALLOW_ORIGINS: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Database
    DATABASE_URL: str = Field(default="postgresql+asyncpg://kyros:kyros@localhost:5432/kyros")
    DB_ECHO: bool = Field(default=False)

    # JWT Authentication
    JWT_SECRET_KEY: str = Field(default="")  # MUST be set in production
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRE_MINUTES: int = Field(default=15)  # 15 minutes (short-lived)
    JWT_REFRESH_EXPIRE_DAYS: int = Field(default=7)  # 7 days for refresh tokens
    
    # Cookie Configuration
    COOKIE_SECURE: bool = Field(default=True)  # Require HTTPS in production
    COOKIE_HTTPONLY: bool = Field(default=True)  # Prevent JavaScript access
    COOKIE_SAMESITE: str = Field(default="lax")  # CSRF protection (lax/strict/none)
    COOKIE_DOMAIN: str | None = Field(default=None)  # Cookie domain (None = current domain)

    # Runtime
    KYROS_STORAGE_DIR: str = Field(default="./storage")
    KYROS_ENV: str = Field(default="dev")
    DEBUG: bool = Field(default=False)
    
    # Rate Limiting
    RATE_LIMIT_RPM: int = Field(default=100, description="Rate limit: requests per minute")
    
    # Cache Settings
    CACHE_TTL_SECONDS: int = Field(default=10, description="Default cache TTL in seconds")
    REDIS_URL: str | None = Field(default=None, description="Redis connection URL")
    
    # Terminal Settings
    MAX_TERMINAL_CONNECTIONS: int = Field(default=50, description="Maximum concurrent terminal connections")
    
    # Workflow Settings
    MAX_CRITIC_ITERATIONS: int = Field(default=3, description="Maximum critic feedback iterations")


settings = Settings()

