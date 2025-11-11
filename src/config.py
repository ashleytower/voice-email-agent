"""
Configuration management for the Voice-First AI Email Agent.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    
    # Google Cloud
    google_application_credentials: Optional[str] = Field(None, env="GOOGLE_APPLICATION_CREDENTIALS")
    google_cloud_project: str = Field(..., env="GOOGLE_CLOUD_PROJECT")
    
    # Supabase
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_key: str = Field(..., env="SUPABASE_KEY")
    supabase_service_key: str = Field(..., env="SUPABASE_SERVICE_KEY")
    
    # Gmail OAuth
    gmail_client_id: str = Field(..., env="GMAIL_CLIENT_ID")
    gmail_client_secret: str = Field(..., env="GMAIL_CLIENT_SECRET")
    gmail_refresh_token: str = Field(..., env="GMAIL_REFRESH_TOKEN")
    
    # Sentry
    sentry_dsn: Optional[str] = Field(None, env="SENTRY_DSN")
    
    # Application
    environment: str = Field("development", env="ENVIRONMENT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
