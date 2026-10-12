"""Application settings loaded from environment variables or Docker secrets."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

_SECRETS_DIR = "/run/secrets"


class Settings(BaseSettings):
    """Application-wide configuration.

    Values come from the environment (or `.env` in development). In production,
    secrets are read from Docker secrets files under /run/secrets.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        secrets_dir=_SECRETS_DIR if os.path.isdir(_SECRETS_DIR) else None,
    )

    brand_name: str = "Nudgeline"
    environment: Literal["development", "test", "staging", "production"] = "development"
    enable_api_docs: bool = False
    cors_origins: str = "http://localhost:3000"
    public_base_url: str = "https://localhost"

    # Database: the app role is subject to row-level security; the system role owns
    # the schema and is used only for migrations, sign-up/login lookups, webhook
    # resolution and the job worker's queue.
    database_url: str = "postgresql+asyncpg://nudgeline_app:nudgeline_app@postgres:5432/nudgeline"
    database_url_system: str = "postgresql+asyncpg://nudgeline:nudgeline@postgres:5432/nudgeline"

    # Auth
    secret_key: str = "change-me-in-production"
    access_token_ttl_minutes: int = 720
    cookie_secure: bool = False

    # Encryption of personal data (base64-encoded 32-byte key)
    encryption_master_key: str = ""

    # Speech service (self-hosted STT/TTS)
    speech_url: str = "http://speech:8000"

    # Telephony
    telephony_backend: Literal["simulated", "livekit"] = "simulated"
    simulated_digit: str = "1"
    simulated_delay_seconds: float = 1.0
    livekit_url: str = "ws://livekit:7880"
    livekit_api_key: str = "devkey"
    livekit_api_secret: str = ""
    livekit_sip_trunk_id: str = ""

    # Worker
    worker_concurrency: int = 5
    worker_poll_seconds: float = 2.0

    # Third-party API versions
    shopify_api_version: str = "2025-07"
    whatsapp_api_version: str = "v22.0"

    @property
    def docs_enabled(self) -> bool:
        """API docs are on in development, and elsewhere only when explicitly enabled."""
        return self.environment == "development" or self.enable_api_docs

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
