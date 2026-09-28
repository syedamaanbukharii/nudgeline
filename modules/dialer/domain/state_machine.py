"""Call lifecycle state machine."""

from __future__ import annotations

from typing import Literal

# States
CallState = Literal[
    "QUEUED",
    "ELIGIBILITY_CHECK",
    "SKIPPED",
    "WAITING_CAPACITY",
    "DIALING",
    "RINGING",
    "CONNECTED",
    "IN_CONVERSATION",
    "TRANSFERRED",
    "ENDED",
    "POST_PROCESSING",
    "CLOSED"
]

# Outcomes on CLOSED
CallOutcome = Literal[
    "MEETING_BOOKED",
    "CALLBACK_REQUESTED",
    "NOT_INTERESTED",
    "WRONG_CONTACT",
    "DO_NOT_CALL",
    "GATEKEEPER",
    "NEEDS_REVIEW"
]


class CallStateMachine:
    """Manages call state transitions."""

    VALID_TRANSITIONS: dict[CallState, set[CallState]] = {
        "QUEUED": {"ELIGIBILITY_CHECK"},
        "ELIGIBILITY_CHECK": {"SKIPPED", "WAITING_CAPACITY"},
        "WAITING_CAPACITY": {"DIALING"},
        "DIALING": {"RINGING", "ENDED"}, # ENDED on failed dial
        "RINGING": {"CONNECTED", "ENDED"}, # ENDED on no answer/voicemail
        "CONNECTED": {"IN_CONVERSATION"},
        "IN_CONVERSATION": {"TRANSFERRED", "ENDED"},
        "TRANSFERRED": {"ENDED"},
        "ENDED": {"POST_PROCESSING"},
        "POST_PROCESSING": {"CLOSED"},
        "SKIPPED": set(),
        "CLOSED": set()
    }

    def __init__(self, initial_state: CallState = "QUEUED"):
        self.state = initial_state

    def transition(self, to_state: CallState) -> None:
        """Transition to a new state."""
        allowed = self.VALID_TRANSITIONS.get(self.state, set())
        if to_state not in allowed:
            raise ValueError(f"Invalid transition from {self.state} to {to_state}")
        self.state = to_state
