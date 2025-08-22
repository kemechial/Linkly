"""
Configuration management with proper environment handling
"""
import os
import secrets
from functools import lru_cache
from pydantic import validator
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App Configuration
    app_name: str = "Linkly API"
    debug: bool = False
    environment: str = "production"
    
    # Security
    secret_key: str  # Must be provided via environment variable
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Database
    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20
    
    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    redis_url: Optional[str] = None
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    auth_rate_limit_per_minute: int = 5
    
    # URL Configuration
    base_url: str = "http://localhost:8000"
    max_url_length: int = 2048
    
    # Monitoring
    sentry_dsn: Optional[str] = None
    enable_metrics: bool = True
    
    @validator('secret_key', pre=True)
    def validate_secret_key(cls, v):
        if not v or v == "your-super-secret-key-change-this-in-production-please":
            if cls.__config__.env_file == ".env" and os.path.exists(".env"):
                # Development mode - generate a warning but allow default
                import warnings
                warnings.warn(
                    "Using default SECRET_KEY in development. "
                    "Change this in production!",
                    UserWarning
                )
                return "your-super-secret-key-change-this-in-production-please-make-it-long-and-random"
            else:
                # Production mode - require proper secret key
                raise ValueError(
                    "SECRET_KEY must be set to a secure random value in production. "
                    "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
                )
        return v
    
    @validator('redis_url', pre=True)
    def build_redis_url(cls, v, values):
        if v:
            return v
        password_part = f":{values['redis_password']}@" if values.get('redis_password') else ""
        return f"redis://{password_part}{values['redis_host']}:{values['redis_port']}/{values['redis_db']}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
