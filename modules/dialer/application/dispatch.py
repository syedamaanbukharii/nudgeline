"""Dialer dispatch service."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from modules.dialer.domain.state_machine import CallStateMachine

if TYPE_CHECKING:
    from modules.compliance.domain.engine import ComplianceEngine
    from modules.contacts.domain.models import Contact
    from modules.dialer.domain.capacity import DialerCapacityManager

logger = logging.getLogger(__name__)


class DialerDispatchService:
    """Orchestrates the dispatch of outbound calls."""

    def __init__(
        self,
        compliance_engine: ComplianceEngine,
        capacity_manager: DialerCapacityManager,
    ):
        self.compliance_engine = compliance_engine
        self.capacity_manager = capacity_manager

    async def dispatch_call(self, campaign_id: str, contact: Contact, campaign_mode: str) -> None:
        """Attempt to dispatch a call to a contact."""
        state_machine = CallStateMachine("QUEUED")

        # 1. Eligibility Check
        state_machine.transition("ELIGIBILITY_CHECK")

        # Simplified for MVP: Check DNC via contact attributes or db lookup
        is_dnc = contact.attrs.get("is_dnc", False)

        decision = await self.compliance_engine.check_eligibility(
            contact=contact, campaign_mode=campaign_mode, is_dnc=is_dnc
        )

        if not decision.allowed:
            logger.info(f"Call skipped for contact {contact.id}: {decision.reason}")
            state_machine.transition("SKIPPED")
            return

        # 2. Wait for Capacity
        state_machine.transition("WAITING_CAPACITY")
        acquired = await self.capacity_manager.acquire_slot(tenant_id=str(contact.tenant_id), campaign_id=campaign_id)

        if not acquired:
            logger.warning(f"No capacity for campaign {campaign_id}")
            # In a real queue, this would stay in WAITING_CAPACITY and retry later.
            return

        # 3. Dialing
        try:
            state_machine.transition("DIALING")
            logger.info(f"Simulating dialing for contact {contact.id} on campaign {campaign_id}")

            # Telephony port call would happen here...

        except Exception as e:
            logger.error(f"Failed to dial: {e}")
            state_machine.transition("ENDED")
        finally:
            await self.capacity_manager.release_slot(tenant_id=str(contact.tenant_id), campaign_id=campaign_id)
