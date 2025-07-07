"""
Application configuration settings.

All configuration is loaded from environment variables or .env file.
"""

import os
from pathlib import Path
from typing import Optional
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


def find_project_root() -> Path:
    """Find project root by looking for .project_root marker file."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".project_root").exists():
            return current
        current = current.parent
    return Path.cwd()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application settings
    PROJECT_NAME: str = Field(default="AI Development Platform", description="Project name")
    VERSION: str = Field(default="0.1.0", description="Application version")
    APP_NAME: str = Field(default="AI Development Platform", description="Application name")
    APP_URL: str = Field(default="http://localhost:3000", description="Frontend application URL")
    API_V1_STR: str = Field(default="/api/v1", description="API version string")
    DEBUG: bool = Field(default=False, description="Debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment name")
    
    # CORS settings
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ai_dev_platform",
        description="PostgreSQL database URL"
    )
    DATABASE_ECHO: bool = Field(
        default=False,
        description="Echo SQL queries (for debugging)"
    )
    
    # JWT settings
    JWT_SECRET: str = Field(
        default="your-secret-key-change-this-in-production",
        description="JWT secret key"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access token expiration in minutes"
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Refresh token expiration in days"
    )
    
    # Email settings (Resend)
    RESEND_API_KEY: str = Field(
        default="re_test_key",
        description="Resend API key"
    )
    EMAIL_FROM: str = Field(
        default="noreply@example.com",
        description="Default from email address"
    )
    EMAIL_FROM_NAME: str = Field(
        default="AI Development Platform",
        description="Default from name"
    )
    
    # Redis settings
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    # AI API settings
    ANTHROPIC_API_KEY: str = Field(
        default="",
        description="Anthropic API key for Claude"
    )
    OPENAI_API_KEY: str = Field(
        default="",
        description="OpenAI API key for GPT"
    )
    GOOGLE_API_KEY: str = Field(
        default="",
        description="Google API key for Gemini"
    )
    
    # Model selection settings
    PRIMARY_MODEL: str = Field(
        default="claude-sonnet-4-20250514",
        description="Primary AI model to use"
    )
    COMPLEX_MODEL: str = Field(
        default="claude-opus-4-20250514",
        description="Model for complex tasks"
    )
    
    # Container settings
    CONTAINER_CPU_LIMIT: str = Field(default="2", description="CPU cores per container")
    CONTAINER_MEMORY_LIMIT: str = Field(default="4g", description="Memory per container")
    CONTAINER_STORAGE_LIMIT: str = Field(default="10g", description="Storage per container")
    CONTAINER_IDLE_TIMEOUT_MINUTES: int = Field(
        default=30,
        description="Minutes before idle container sleeps"
    )
    
    # User limits
    DEFAULT_MONTHLY_TOKEN_LIMIT: int = Field(
        default=1_000_000,
        description="Default monthly token limit per user"
    )
    DEFAULT_MONTHLY_COST_LIMIT_USD: float = Field(
        default=50.0,
        description="Default monthly cost limit per user in USD"
    )
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    
    # AI Model configurations
    CLAUDE_DEFAULT_MODEL: str = Field(
        default="claude-sonnet-4-20250514",
        description="Default Claude model for routine tasks (Claude 4 Sonnet)"
    )
    CLAUDE_COMPLEX_MODEL: str = Field(
        default="claude-opus-4-20250514", 
        description="Claude model for complex tasks (Claude 4 Opus)"
    )
    CLAUDE_API_KEY: str = Field(
        default=os.getenv("CLAUDE_API_KEY", ""),
        description="Anthropic Claude API key"
    )
    OPENAI_API_KEY: str = Field(
        default=os.getenv("OPENAI_API_KEY", ""),
        description="OpenAI API key for fallback"
    )
    GEMINI_API_KEY: str = Field(
        default=os.getenv("GEMINI_API_KEY", ""),
        description="Google Gemini API key for fallback"
    )
    
    @field_validator("DATABASE_URL")
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL uses asyncpg for async operations."""
        if "postgresql://" in v and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://")
        return v
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def sync_database_url(self) -> str:
        """Get synchronous database URL for Alembic."""
        return self.DATABASE_URL.replace("+asyncpg", "")
    
    class Config:
        """Pydantic config."""
        env_file = str(find_project_root() / ".env")
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Create settings instance
settings = get_settings() 