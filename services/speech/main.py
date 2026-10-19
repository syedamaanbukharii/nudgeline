"""Self-hosted speech service.

POST /tts  {"text": "...", "language": "ar"|"en"}  -> 16 kHz 16-bit mono WAV
POST /stt  multipart audio file (+ optional language) -> {"text": "..."}

Backends (env):
  TTS_BACKEND=chatterbox  Chatterbox Multilingual (MIT, supports Arabic). Default.
  TTS_BACKEND=tone        A short beep pattern; no model download. For development.
  STT_BACKEND=whisper     faster-whisper (MIT). STT_MODEL defaults to large-v3-turbo.
  STT_BACKEND=none        Disables /stt.
"""

from __future__ import annotations

import asyncio
import io
import math
import os
import struct
import tempfile
import wave
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

OUTPUT_RATE = 16000
TTS_BACKEND = os.getenv("TTS_BACKEND", "chatterbox")
STT_BACKEND = os.getenv("STT_BACKEND", "whisper")
DEVICE = os.getenv("DEVICE", "cpu")

app = FastAPI(title="speech", docs_url=None, redoc_url=None, openapi_url=None)
_lock = asyncio.Lock()  # one synthesis at a time keeps memory predictable on small servers


class TTSIn(BaseModel):
    text: str = Field(min_length=1, max_length=800)
    language: str = Field(pattern="^(ar|en)$")


def _wav(samples: list[float] | Any, rate: int) -> bytes:
    """Encode float samples in [-1, 1] as 16-bit mono WAV at OUTPUT_RATE."""
    import numpy as np

    data = np.asarray(samples, dtype=np.float32).flatten()
    if rate != OUTPUT_RATE:
        duration = len(data) / rate
        target = np.linspace(0, len(data) - 1, int(duration * OUTPUT_RATE))
        data = np.interp(target, np.arange(len(data)), data).astype(np.float32)
    pcm = (np.clip(data, -1.0, 1.0) * 32767).astype("<i2").tobytes()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(OUTPUT_RATE)
        out.writeframes(pcm)
    return buf.getvalue()


def _tone(text: str) -> bytes:
    """Development stand-in: one 200 ms beep per 40 characters."""
    beeps = max(1, min(len(text) // 40, 8))
    frames = bytearray()
    for _ in range(beeps):
        for i in range(int(OUTPUT_RATE * 0.2)):
            frames += struct.pack("<h", int(8000 * math.sin(2 * math.pi * 660 * i / OUTPUT_RATE)))
        frames += b"\x00\x00" * int(OUTPUT_RATE * 0.15)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(OUTPUT_RATE)
        out.writeframes(bytes(frames))
    return buf.getvalue()


@lru_cache(maxsize=1)
def _chatterbox() -> Any:
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    return ChatterboxMultilingualTTS.from_pretrained(device=DEVICE)


@lru_cache(maxsize=1)
def _whisper() -> Any:
    from faster_whisper import WhisperModel

    return WhisperModel(
        os.getenv("STT_MODEL", "large-v3-turbo"), device=DEVICE, compute_type=os.getenv("STT_COMPUTE", "int8")
    )


def _synthesize(text: str, language: str) -> bytes:
    if TTS_BACKEND == "tone":
        return _tone(text)
    model = _chatterbox()
    audio = model.generate(text, language_id=language)
    return _wav(audio.squeeze().cpu().numpy(), model.sr)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "tts": TTS_BACKEND, "stt": STT_BACKEND}


@app.post("/tts")
async def tts(body: TTSIn) -> Response:
    async with _lock:
        wav = await asyncio.to_thread(_synthesize, body.text, body.language)
    return Response(content=wav, media_type="audio/wav")


@app.post("/stt")
async def stt(file: UploadFile = File(...), language: str | None = Form(default=None)) -> dict[str, str]:
    if STT_BACKEND == "none":
        raise HTTPException(status_code=503, detail="Speech-to-text is disabled")
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Audio too large")
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        tmp.write(data)
        tmp.flush()

        def run() -> str:
            segments, _ = _whisper().transcribe(tmp.name, language=language, vad_filter=True)
            return " ".join(s.text.strip() for s in segments)

        async with _lock:
            text = await asyncio.to_thread(run)
    return {"text": text}
