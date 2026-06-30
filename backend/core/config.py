from typing import Any, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator

class Settings(BaseSettings):
    # Database and Caching
    DATABASE_URL: str = "postgresql+asyncpg://user:password@host/dbname"
    REDIS_URL: str = "redis://localhost:6379/0"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_POOL_RECYCLE: int = 300  # seconds — prevents stale connections on cloud DBs
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    USE_CELERY: bool = False
    
    # Authentication
    SECRET_KEY: str = "change-me-temporary-key-that-is-at-least-32-chars-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    API_KEY_HASH_SALT: str = ""  # Deterministic bcrypt salt for API key hashing — set in production
    
    # WarriorPlus Integration — PRIMARY SUBSCRIPTION GATEWAY
    WARRIORPLUS_SECURITY_KEY: str = ""
    WARRIORPLUS_PRO_PRODUCT_ID: str = ""       # WarriorPlus product/offer ID for Pro tier
    WARRIORPLUS_ENTERPRISE_PRODUCT_ID: str = "" # WarriorPlus product/offer ID for Enterprise tier
    SUBSCRIPTION_PERIOD_DAYS: int = 30          # Default subscription period in days
    
    # PayPal Integration — WALLET TOP-UP GATEWAY
    PAYPAL_CLIENT_ID: str = ""
    PAYPAL_CLIENT_SECRET: str = ""
    PAYPAL_WEBHOOK_ID: str = ""
    PAYPAL_MODE: str = "sandbox"                # "sandbox" or "live"
    PAYPAL_WALLET_TOPUP_AMOUNTS: str = "5,20,50,100"  # Comma-separated allowed credit amounts (USD)
    
    # External APIs
    GEMINI_API_KEY: str = ""
    RAPIDAPI_PROXY_SECRET: str = ""
    META_ACCESS_TOKEN: str = ""
    META_PIXEL_ID: str = ""
    
    # Environment Configurations
    ALLOWED_ORIGINS: str = ""
    FRONTEND_URL: str = "https://quantcai.in"
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"
    MAX_REQUEST_SIZE_BYTES: int = 1_048_576  # 1MB — prevents oversized QASM/payload attacks
    ENABLE_REAL_QPU: bool = False
    
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
        if v not in ("development", "staging", "production"):
            raise ValueError("ENVIRONMENT must be 'development', 'staging', or 'production'")
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @model_validator(mode="after")
    def validate_prod_secrets(self):
        """Enforce that critical secrets are set in production."""
        if self.ENVIRONMENT == "production":
            if "change-me" in self.SECRET_KEY:
                raise ValueError(
                    "SECRET_KEY contains 'change-me' — this is unsafe for production. "
                    "Set a strong, random SECRET_KEY environment variable."
                )
            if not self.WARRIORPLUS_SECURITY_KEY:
                import logging
                logging.getLogger(__name__).warning(
                    "WARRIORPLUS_SECURITY_KEY is not set — subscription IPN will reject all requests."
                )
        return self

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_staging(self) -> bool:
        return self.ENVIRONMENT == "staging"

    @property
    def cors_origins(self) -> list[str]:
        origins = [
            "https://quantcai.in",
            "https://www.quantcai.in",
            "http://localhost:5173",
            "http://localhost:3000"
        ]
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL)
            
        if self.ALLOWED_ORIGINS:
            for origin in self.ALLOWED_ORIGINS.split(","):
                clean_origin = origin.strip()
                if clean_origin and clean_origin not in origins:
                    origins.append(clean_origin)
                    
        return origins

    @property
    def wallet_topup_amounts(self) -> list[int]:
        """Parsed list of allowed wallet top-up amounts in USD."""
        return [int(a.strip()) for a in self.PAYPAL_WALLET_TOPUP_AMOUNTS.split(",") if a.strip().isdigit()]

    # -------------------------------------------------------------------------
    # Centralized Tier Limits — single source of truth for all enforcement
    # -------------------------------------------------------------------------
    TIER_LIMITS: dict = {
        "FREE": {
            "max_qubits": 3,
            "max_depth": 15,
            "max_shots": 1024,
            "noise_models": ["ideal"],
            "statevector_access": False,
            "daily_circuit_runs": 10,
            "daily_ai_chats": 10,
            "monthly_pqc_scans": 3,
            "daily_api_requests": 10,
            "max_concurrent_jobs": 1,
            "max_api_keys": 5,
        },
        "PRO": {
            "max_qubits": 15,
            "max_depth": 999999,
            "max_shots": 65536,
            "noise_models": ["ideal", "depolarizing", "thermal"],
            "statevector_access": True,
            "daily_circuit_runs": 500,
            "daily_ai_chats": 999999,
            "monthly_pqc_scans": 50,
            "daily_api_requests": 500,
            "max_concurrent_jobs": 5,
            "max_api_keys": 20,
        },
        "API_METERED": {
            "max_qubits": 15,
            "max_depth": 999999,
            "max_shots": 65536,
            "noise_models": ["ideal", "depolarizing", "thermal"],
            "statevector_access": True,
            "daily_circuit_runs": 999999,
            "daily_ai_chats": 999999,
            "monthly_pqc_scans": 50,
            "daily_api_requests": 999999,
            "max_concurrent_jobs": 10,
            "max_api_keys": 50,
        },
        "INSTITUTIONAL": {
            "max_qubits": 25,
            "max_depth": 999999,
            "max_shots": 65536,
            "noise_models": ["ideal", "depolarizing", "thermal"],
            "statevector_access": True,
            "daily_circuit_runs": 999999,
            "daily_ai_chats": 999999,
            "monthly_pqc_scans": 999999,
            "daily_api_requests": 999999,
            "max_concurrent_jobs": 20,
            "max_api_keys": 100,
        },
        "ENTERPRISE": {
            "max_qubits": 29,
            "max_depth": 999999,
            "max_shots": 65536,
            "noise_models": ["ideal", "depolarizing", "thermal"],
            "statevector_access": True,
            "daily_circuit_runs": 999999,
            "daily_ai_chats": 999999,
            "monthly_pqc_scans": 999999,
            "daily_api_requests": 100000,
            "max_concurrent_jobs": 20,
            "max_api_keys": 100,
        },
    }

settings = Settings()
