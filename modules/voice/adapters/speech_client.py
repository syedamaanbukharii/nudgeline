"""Client for the self-hosted speech service (TTS now; STT for the AI fallback later)."""

from __future__ import annotations

import hashlib
import io
import wave
from collections import OrderedDict
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class Audio:
    pcm: bytes  # 16-bit little-endian mono
    sample_rate: int

    @property
    def duration_seconds(self) -> float:
        return len(self.pcm) / 2 / self.sample_rate


def decode_wav(data: bytes) -> Audio:
    with wave.open(io.BytesIO(data), "rb") as wav:
        if wav.getsampwidth() != 2 or wav.getnchannels() != 1:
            raise ValueError("speech service must return 16-bit mono WAV")
        return Audio(wav.readframes(wav.getnframes()), wav.getframerate())


class SpeechClient:
    """Fetches synthesized prompts and keeps the most recent ones in memory."""

    def __init__(self, base_url: str, cache_size: int = 256, timeout: float = 60) -> None:
        self._base = base_url.rstrip("/")
        self._cache: OrderedDict[str, Audio] = OrderedDict()
        self._size = cache_size
        self._timeout = timeout

    async def synthesize(self, text: str, language: str) -> Audio:
        key = hashlib.sha256(f"{language}:{text}".encode()).hexdigest()
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(f"{self._base}/tts", json={"text": text, "language": language})
        response.raise_for_status()
        audio = decode_wav(response.content)
        self._cache[key] = audio
        if len(self._cache) > self._size:
            self._cache.popitem(last=False)
        return audio
