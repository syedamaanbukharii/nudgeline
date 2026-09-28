"""Sequence application logic."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SequenceService:
    """Manages email sequences, approvals, and stop rules."""

    def __init__(self, email_port: Any):
        self.email_port = email_port

    async def approve_draft(self, message_id: str) -> bool:
        """Approve an email draft for sending."""
        logger.info(f"Approving email draft {message_id}")
        # In MVP, this would mark the message as approved and queue a job
        # to send it via the email port.
        return True

    async def reject_draft(self, message_id: str) -> bool:
        """Reject an email draft."""
        logger.info(f"Rejecting email draft {message_id}")
        return True

    async def process_reply_webhook(self, thread_id: str) -> None:
        """Handle an incoming reply webhook from Gmail/Graph.
        
        This triggers stop rules for any active sequence enrollments.
        """
        logger.info(f"Received reply for thread {thread_id}. Applying stop rules.")
        # Logic: 
        # 1. Find EmailMessage by thread_id
        # 2. Update replied_at
        # 3. Find SequenceEnrollment
        # 4. Mark state as 'stopped_replied'
        pass

    async def run_next_step(self, enrollment_id: str) -> None:
        """Execute the next step in a sequence."""
        logger.info(f"Running next step for enrollment {enrollment_id}")
        # Logic:
        # 1. Check if enrollment is active
        # 2. Check stop rules (e.g., if a meeting was booked, stop)
        # 3. Generate draft for current_step
        # 4. If campaign allows auto-send, send it. Else, mark as draft.
        # 5. Schedule next step via scheduled_actions
        pass
