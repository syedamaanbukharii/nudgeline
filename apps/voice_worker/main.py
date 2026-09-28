"""Nudgeline Voice Worker (LiveKit Agents)."""

import asyncio
import logging
import os

from livekit.agents import AutoSubscribe, JobContext, JobProcess, WorkerOptions, cli, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, silero

from modules.tenancy.domain.settings import get_settings

logger = logging.getLogger(__name__)

# Define the allowed tools for the agent
class NudgelineTools(llm.FunctionContext):
    """The six allow-listed tools for the voice agent."""
    
    @llm.ai_callable(description="Get available meeting slots for the assigned rep.")
    async def get_slots(self, timezone: str) -> str:
        # Mock logic
        return "Tuesday at 2 PM, Wednesday at 10 AM"

    @llm.ai_callable(description="Book a meeting into the rep's calendar.")
    async def book_meeting(self, slot_id: str) -> str:
        return "Meeting booked successfully."

    @llm.ai_callable(description="Set a callback reminder for the rep to call the contact back.")
    async def set_callback(self, due_at: str, note: str) -> str:
        return "Callback reminder set."

    @llm.ai_callable(description="Mark the contact as Do Not Call (DNC).")
    async def mark_dnc(self) -> str:
        return "Contact marked as Do Not Call."

    @llm.ai_callable(description="Transfer the call to a human representative.")
    async def transfer_to_human(self) -> str:
        return "Transferring call now."

    @llm.ai_callable(description="End the call.")
    async def end_call(self) -> str:
        return "Ending call."


def preflight(ctx: JobContext):
    """Runs before the agent joins the room."""
    # Pre-fetch CRM brief and free/busy here in a real scenario
    pass


async def entrypoint(ctx: JobContext):
    """Entrypoint for the voice agent."""
    logger.info(f"Agent starting in room {ctx.room.name}")
    
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # In production, STT and TTS would point to our custom services via a custom LiveKit plugin.
    # Here we mock it with OpenAI plugins configured to point to our local/fake endpoints,
    # or just use the default OpenAI plugin if keys are missing (they will fail gracefully).
    
    agent = VoicePipelineAgent(
        vad=silero.VAD.load(),
        stt=openai.STT(), # Would be our custom faster-whisper STT port
        llm=openai.LLM(model="llama3-8b-8192"), # Would use Groq via LLM Gateway
        tts=openai.TTS(), # Would be our custom Kokoro TTS port
        fnc_ctx=NudgelineTools(),
        chat_ctx=llm.ChatContext().append(
            role="system",
            text=(
                "You are an AI voice assistant calling on behalf of Nudgeline. "
                "Disclose that you are an AI in your first sentence. "
                "Keep responses brief and conversational."
            ),
        ),
    )

    agent.start(ctx.room)
    
    await asyncio.sleep(1)
    await agent.say("Hi, I'm an AI calling on behalf of Nudgeline. How are you today?", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            preflight_fnc=preflight,
        )
    )
