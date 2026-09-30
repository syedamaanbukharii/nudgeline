"""Text-to-Speech (TTS) service entry point.

Uses Kokoro for TTS.
"""

import logging

from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel

app = FastAPI(title="Nudgeline TTS Service")
logger = logging.getLogger(__name__)


class TTSRequest(BaseModel):
    text: str
    voice: str = "default"


@app.post("/v1/synthesize")
async def synthesize(request: TTSRequest):
    """Synthesize text into speech."""
    logger.info(f"Synthesizing text with voice {request.voice}")

    # MVP: Mock audio generation (return empty wav headers or just a dummy byte string)
    dummy_audio_bytes = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"  # noqa: E501

    return Response(content=dummy_audio_bytes, media_type="audio/wav")


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
