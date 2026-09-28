"""Gemini Live API native voice worker for Nudgeline."""

import asyncio
import logging
import os
import wave
from typing import Callable, Any

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# --- Nudgeline Tools ---

def get_slots(timezone: str) -> str:
    """Get available meeting slots for the assigned rep."""
    return "Tuesday at 2 PM, Wednesday at 10 AM"

def book_meeting(slot_id: str) -> str:
    """Book a meeting into the rep's calendar."""
    return "Meeting booked successfully."

def set_callback(due_at: str, note: str) -> str:
    """Set a callback reminder for the rep to call the contact back."""
    return "Callback reminder set."

def mark_dnc() -> str:
    """Mark the contact as Do Not Call (DNC)."""
    return "Contact marked as Do Not Call."

def transfer_to_human() -> str:
    """Transfer the call to a human representative."""
    return "Transferring call now."

def end_call() -> str:
    """End the call."""
    return "Ending call."


class GeminiLiveVoiceWorker:
    """Native Voice Worker using Gemini Live API."""

    def __init__(self, api_key: str | None = None):
        self.client = genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))
        self.model = "gemini-3.1-flash-live-preview"
        
        self.config = types.LiveConnectConfig(
            response_modalities=[types.Modality.AUDIO],
            system_instruction=types.Content(
                parts=[
                    types.Part.from_text(
                        "You are an AI voice assistant calling on behalf of Nudgeline. "
                        "Disclose that you are an AI in your first sentence. "
                        "Keep responses brief, conversational, and natural."
                    )
                ]
            ),
            tools=[get_slots, book_meeting, set_callback, mark_dnc, transfer_to_human, end_call]
        )

    async def start_session(self):
        """Connects to Gemini Live API and starts the bidirectional session."""
        logger.info(f"Connecting to {self.model}...")
        
        async with self.client.aio.live.connect(model=self.model, config=self.config) as session:
            logger.info("Session established.")
            
            # Start concurrent send and receive tasks
            receive_task = asyncio.create_task(self._receive_loop(session))
            
            try:
                # E.g. Send a simulated microphone stream
                await asyncio.sleep(600)  # Keep session alive for 10 minutes max
            except asyncio.CancelledError:
                logger.info("Session cancelled.")
            finally:
                receive_task.cancel()

    async def _receive_loop(self, session):
        """Process incoming audio, transcriptions, and tool calls."""
        try:
            async for response in session.receive():
                content = response.server_content
                if not content:
                    continue

                # 1. Process Audio Output (Raw PCM 24kHz)
                if content.model_turn:
                    for part in content.model_turn.parts:
                        if part.inline_data:
                            # audio_data = part.inline_data.data
                            # Route to speaker/telephony
                            pass
                        elif part.function_call:
                            # Handle synchronous tool use
                            func_name = part.function_call.name
                            func_args = part.function_call.args
                            logger.info(f"Model called function: {func_name} with {func_args}")
                            
                            # Execute local function and return result (simplified)
                            tool_result = {"status": "ok"}
                            await session.send_realtime_input(
                                text=f"Function {func_name} executed. Result: {tool_result}"
                            )

                # 2. Process Transcriptions
                if content.input_transcription:
                    logger.info(f"User: {content.input_transcription.text}")
                if content.output_transcription:
                    logger.info(f"Gemini: {content.output_transcription.text}")
                    
                # 3. Handle Interruptions
                if content.interrupted:
                    logger.info("VAD Interruption detected. Halting playback.")
                    # Flush telephony playback queue here

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in receive loop: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    worker = GeminiLiveVoiceWorker()
    asyncio.run(worker.start_session())
