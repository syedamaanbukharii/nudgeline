"""Speech-to-text service (faster-whisper)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

app = FastAPI(
    title="Nudgeline STT Service",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    default_response_class=ORJSONResponse,
)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
