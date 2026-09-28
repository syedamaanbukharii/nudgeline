"""Compliance engine."""

from __future__ import annotations

import zoneinfo
from datetime import datetime, time
from typing import TYPE_CHECKING

from modules.compliance.domain.models import ComplianceDecision

if TYPE_CHECKING:
    from modules.contacts.domain.models import Contact


class ComplianceEngine:
    """Engine to check dial eligibility."""

    async def check_eligibility(
        self, contact: Contact, campaign_mode: str, is_dnc: bool
    ) -> ComplianceDecision:
        """Check if a contact can be dialed.
        
        Args:
            contact: The contact to check.
            campaign_mode: 'A', 'B', or 'C'
            is_dnc: Whether the contact's phone hash is in the DNC list.
        """
        # 1. Check if DNC
        if is_dnc:
            return ComplianceDecision(allowed=False, reason="Contact is on DNC list")
        
        # 2. Check consent for Mode A (AI voice calls)
        if campaign_mode == "A":
            has_voice_consent = any(
                c.channel == "voice" and not c.revoked_at 
                for c in contact.consents
            )
            if not has_voice_consent:
                return ComplianceDecision(
                    allowed=False, reason="Missing required voice consent for Mode A"
                )
            
        # 3. Check calling window (8 AM to 5 PM local time)
        try:
            tz = zoneinfo.ZoneInfo(contact.timezone)
        except Exception:
            tz = zoneinfo.ZoneInfo("UTC")
            
        now_local = datetime.now(tz)
        local_time = now_local.time()
        
        if not (time(8, 0) <= local_time <= time(17, 0)):
            return ComplianceDecision(
                allowed=False, reason="Outside of allowed calling window (8 AM - 5 PM local)"
            )
            
        return ComplianceDecision(allowed=True, reason="Allowed")
