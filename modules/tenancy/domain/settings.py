"""Application settings loaded from environment."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://nudgeline:nudgeline@pgbouncer:6432/nudgeline"
    database_url_sync: str = "postgresql://nudgeline:nudgeline@pgbouncer:6432/nudgeline"

    # Valkey
    valkey_url: str = "valkey://valkey:6379/0"

    # Keycloak
    keycloak_url: str = "http://keycloak:8080"
    keycloak_realm: str = "nudgeline"
    keycloak_client_id: str = "nudgeline-api"
    keycloak_client_secret: str = "change-me"

    # LiveKit
    livekit_url: str = "ws://livekit:7880"
    livekit_api_key: str = "devkey"
    livekit_api_secret: str = "devsecret"

    # Object storage
    s3_endpoint_url: str = "http://seaweedfs:8333"
    s3_access_key: str = "admin"
    s3_secret_key: str = "admin"
    s3_bucket_recordings: str = "recordings"
    s3_bucket_transcripts: str = "transcripts"

    # LLM providers
    groq_api_key: str = ""
    gemini_api_key: str = ""

    # Observability
    glitchtip_dsn: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://langfuse:3001"

    # App
    environment: str = "development"
    enable_api_docs: bool = True
    cors_origins: str = "http://localhost:3000"
    secret_key: str = "change-me-in-production"

    # Encryption
    encryption_master_key: str = "base64-encoded-32-byte-key-here"

    # Rate limits
    rate_limit_per_key: int = Field(default=100, description="Requests per minute per API key")
    rate_limit_per_tenant: int = Field(default=1000, description="Requests per minute per tenant")


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
