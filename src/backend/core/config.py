"""
Configuration settings for the AI Development Platform.

Uses Pydantic Settings for environment variable management.
"""

from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App Configuration
    APP_NAME: str = "AI Development Platform"
    DEBUG: bool = False
    VERSION: str = "0.1.0"
    
    # Security
    SECRET_KEY: str = Field(..., description="Secret key for JWT signing")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL database URL")
    DATABASE_ECHO: bool = False
    
    # Redis
    REDIS_URL: str = Field(..., description="Redis connection URL")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # LLM API Keys
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic Claude API key")
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    
    # Email (Resend)
    RESEND_API_KEY: str = Field(default="", description="Resend email API key")
    FROM_EMAIL: str = "noreply@zeblit.ai"
    
    # Container Management
    CONTAINER_BASE_IMAGE: str = "python:3.12-slim"
    CONTAINER_TIMEOUT_MINUTES: int = 30
    MAX_CONTAINERS_PER_USER: int = 3
    
    # File System
    UPLOAD_MAX_SIZE_MB: int = 100
    ALLOWED_FILE_TYPES: List[str] = [
        ".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yaml", ".yml",
        ".md", ".txt", ".html", ".css", ".sql", ".env"
    ]
    
    # Cost Tracking
    MAX_MONTHLY_COST_USD: float = 100.0
    COST_ALERT_THRESHOLD_USD: float = 80.0
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings() 