"""CRM integration port."""

from __future__ import annotations

from typing import Any, Protocol


class CRMPort(Protocol):
    """Port for pushing/pulling data to/from external CRMs (HubSpot, Salesforce, GoHighLevel)."""

    async def get_contact(self, external_id: str) -> dict[str, Any]:
        """Fetch a contact from the CRM."""
        ...

    async def create_or_update_contact(self, data: dict[str, Any]) -> str:
        """Create or update a contact, returning the CRM's ID."""
        ...

    async def log_activity(self, contact_id: str, activity_type: str, details: dict[str, Any]) -> None:
        """Log a call, email, or meeting to the contact's CRM timeline."""
        ...
