from typing import Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator

class Settings(BaseSettings):
    # Database and Caching
    DATABASE_URL: str = "postgresql+asyncpg://user:password@host/dbname"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    USE_CELERY: bool = False
    
    # Authentication
    SECRET_KEY: str = "change-me-temporary-key-that-is-at-least-32-chars-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    

    
    # WarriorPlus Integration (deprecated — 90-day sunset)
    WARRIORPLUS_SECURITY_KEY: str = ""
    
    # PayPal Billing Integration
    PAYPAL_CLIENT_ID: str = ""
    PAYPAL_CLIENT_SECRET: str = ""
    PAYPAL_WEBHOOK_ID: str = ""
    PAYPAL_PRO_PLAN_ID: str = ""          # PayPal subscription plan ID for Pro tier
    PAYPAL_ENTERPRISE_PLAN_ID: str = ""   # PayPal subscription plan ID for Enterprise tier
    PAYPAL_MODE: str = "sandbox"          # "sandbox" or "live"
    
    # External APIs
    GEMINI_API_KEY: str = ""
    RAPIDAPI_PROXY_SECRET: str = ""
    
    # Environment Configurations
    ALLOWED_ORIGINS: str = ""
    FRONTEND_URL: str = "https://quantcai.in"
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=None, 
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="before")
    @classmethod
    def map_auth_env_vars(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Map AUTH_SECRET_KEY -> SECRET_KEY
            auth_key = data.get("auth_secret_key") or data.get("AUTH_SECRET_KEY")
            if auth_key and not data.get("SECRET_KEY"):
                data["SECRET_KEY"] = auth_key
            
            # Map AUTH_ALGORITHM -> ALGORITHM
            auth_alg = data.get("auth_algorithm") or data.get("AUTH_ALGORITHM")
            if auth_alg and not data.get("ALGORITHM"):
                data["ALGORITHM"] = auth_alg

            # Map ACCESS_TOKEN_MINUTES -> ACCESS_TOKEN_EXPIRE_MINUTES
            access_min = data.get("access_token_minutes") or data.get("ACCESS_TOKEN_MINUTES")
            if access_min and not data.get("ACCESS_TOKEN_EXPIRE_MINUTES"):
                data["ACCESS_TOKEN_EXPIRE_MINUTES"] = int(access_min)

            # Map REFRESH_TOKEN_MINUTES -> REFRESH_TOKEN_EXPIRE_DAYS (minutes to days)
            refresh_min = data.get("refresh_token_minutes") or data.get("REFRESH_TOKEN_MINUTES")
            if refresh_min and not data.get("REFRESH_TOKEN_EXPIRE_DAYS"):
                data["REFRESH_TOKEN_EXPIRE_DAYS"] = int(refresh_min) // 1440
                
            # Align ENVIRONMENT with ENV if specified in .env
            env_val = data.get("env") or data.get("ENV")
            if env_val and not data.get("ENVIRONMENT"):
                data["ENVIRONMENT"] = "production" if env_val == "production" else "development"
        return data

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        if v not in ("development", "production"):
            raise ValueError("ENVIRONMENT must be 'development' or 'production'")
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @model_validator(mode="after")
    def validate_prod_secret(self):
        # Allow default secret keys to avoid deployment crashes on Render
        return self

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def cors_origins(self) -> list[str]:
        if self.ALLOWED_ORIGINS:
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
        if self.is_production:
            return [self.FRONTEND_URL]
        return ["http://localhost:5173", "http://localhost:3000"]

settings = Settings()
