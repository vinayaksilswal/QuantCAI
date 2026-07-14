"""
=============================================================================
QuantCAI — Centralized Configuration (Pydantic Settings)
=============================================================================
All environment variables are loaded here via pydantic-settings and exposed
as a singleton `settings` instance. Every service imports from this module
instead of calling os.getenv() directly.

Environment variables are loaded from the .env file in the python_admin/
directory (or the root .env via env_file config).
=============================================================================
"""

from __future__ import annotations

import warnings
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All fields use snake_case; pydantic-settings auto-maps to UPPER_CASE env vars.
    """

    # =========================================================================
    # Core Application
    # =========================================================================
    environment: str = "development"
    allowed_origins: list[str] = ["*"]

    # =========================================================================
    # Database (PostgreSQL via Prisma)
    # =========================================================================
    database_url: str

    # =========================================================================
    # Admin Authentication (JWT-based cookie auth)
    # =========================================================================
    admin_username: str
    admin_password: str
    jwt_secret: str | None = None
    jwt_algorithm: str = "HS256"


    # =========================================================================
    # OpenRouter API (LLM — AI copy generation & chatbot)
    # =========================================================================
    openrouter_api_key: str | None = None

    # =========================================================================
    # Meta Graph API (Facebook + Instagram publishing)
    # =========================================================================
    fb_page_access_token: str | None = None
    fb_page_id: str | None = None
    ig_business_account_id: str | None = None

    # =========================================================================
    # Resend API (Transactional & Marketing Email)
    # =========================================================================
    resend_api_key: str | None = None
    resend_from_email: str = "QuantCAI <support@quantcai.in>"

    # =========================================================================
    # Gemini API Key (legacy — kept for backward compat if needed)
    # =========================================================================
    gemini_api_key: str | None = None

    # =========================================================================
    # Pydantic Settings Configuration
    # =========================================================================
    model_config = SettingsConfigDict(
        # Look for .env in the parent directory (project root) first,
        # then fall back to the python_admin/.env
        env_file=("../.env", ".env"),
        extra="ignore",  # Ignore unknown env vars (e.g., VITE_*)
    )

    @model_validator(mode="after")
    def validate_security(self) -> "Settings":
        if self.environment == "production":
            if not self.jwt_secret or self.jwt_secret == "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7":
                raise ValueError("CRITICAL: JWT_SECRET must be securely set in production environment variables.")
        elif not self.jwt_secret:
            self.jwt_secret = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
            warnings.warn("Using default JWT_SECRET for development. Do NOT use in production.")
        return self


# =============================================================================
# Global Singleton Instance
# =============================================================================
settings = Settings()
