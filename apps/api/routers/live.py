"""Live call events via Server-Sent Events (SSE)."""

import asyncio
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/v1/live", tags=["live"])


async def call_event_generator(call_id: str, request: Request):
    """Yield SSE events for a specific call."""
    # Simulate connection setup
    yield {"event": "connected", "data": "Streaming started"}
    
    try:
        while True:
            # If client disconnects, request.is_disconnected() is True
            if await request.is_disconnected():
                break
                
            # MVP Mock: Yield a heartbeat or simulated transcript delta every 5 seconds
            # In production, this would subscribe to a Redis pub/sub channel for the call
            await asyncio.sleep(5)
            yield {
                "event": "transcript",
                "data": '{"role": "agent", "text": "Are you still there?"}'
            }
    except asyncio.CancelledError:
        pass


@router.get("/calls/{call_id}/stream")
async def stream_call(call_id: str, request: Request):
    """Stream live transcript and events for an active call."""
    # Authenticate via request.state.tenant_id
    
    return EventSourceResponse(call_event_generator(call_id, request))
