"""Email port."""

from __future__ import annotations

from typing import Protocol, Any


class EmailPort(Protocol):
    """Port for sending and reading emails via external providers (Gmail/Graph)."""

    async def send_email(self, message: dict[str, Any]) -> str:
        """Send an email from the rep's mailbox.
        
        Args:
            message: Dictionary containing to, subject, body, etc.
            
        Returns:
            Provider message ID.
        """
        ...

    async def watch_replies(self, user_id: str) -> dict[str, Any]:
        """Subscribe to reply notifications for a user's mailbox."""
        ...

    async def renew_subscription(self, subscription_id: str) -> dict[str, Any]:
        """Renew an existing push subscription."""
        ...
