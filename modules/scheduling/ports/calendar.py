"""Calendar ports."""

from __future__ import annotations

from typing import Protocol, Any


class CalendarPort(Protocol):
    """Port for interacting with external calendars (Google/Microsoft)."""

    async def free_busy(self, user_id: str, start_time: str, end_time: str) -> list[dict[str, Any]]:
        """Fetch free/busy slots for a given user."""
        ...

    async def create_meeting(self, req: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        """Create a new calendar event with a video conference link."""
        ...

    async def cancel_meeting(self, meeting_id: str) -> None:
        """Cancel an existing calendar event."""
        ...
