"""Nudgeline API entry point."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from apps.api.middleware.errors import register_error_handlers
from apps.api.middleware.logging import configure_logging
from apps.api.middleware.request_id import RequestIDMiddleware
from modules.tenancy.domain.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Handle startup and shutdown."""
    settings = get_settings()
    configure_logging(json_output=settings.environment != "development")
    yield


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()
    enable_docs = settings.enable_api_docs

    app = FastAPI(
        title="Nudgeline API",
        version="0.1.0",
        docs_url="/docs" if enable_docs else None,
        redoc_url="/redoc" if enable_docs else None,
        openapi_url="/openapi.json" if enable_docs else None,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # Middleware (order matters: outermost first)
    app.add_middleware(RequestIDMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from apps.api.routers import campaigns, live, webhooks
    app.include_router(campaigns.router)
    app.include_router(live.router)
    app.include_router(webhooks.router)

    register_error_handlers(app)

    @app.get("/healthz", tags=["system"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
