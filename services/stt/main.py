"""Speech-to-Text (STT) service entry point.

Uses faster-whisper.
"""

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import logging

# Note: In a real environment, we would load faster_whisper.WhisperModel here.
# For this MVP without GPU/heavy dependencies, we mock the inference.

app = FastAPI(title="Nudgeline STT Service")
logger = logging.getLogger(__name__)

@app.post("/v1/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """Transcribe an audio file."""
    # MVP: Mock transcription
    logger.info(f"Received audio file {audio.filename} for transcription")
    
    return JSONResponse({
        "text": "This is a simulated transcription.",
        "language": "en",
        "confidence": 0.99
    })

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
