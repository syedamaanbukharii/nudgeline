"""A fake phone line for development and demos. No calls leave the machine.

Behaviour by the number's last digits, so every path can be exercised:
  ...00 -> no answer   ...01 -> busy   ...02 -> answered, no key pressed
  ...99 -> presses 2 (cancel)          anything else -> presses SIMULATED_DIGIT (default 1)
"""

from __future__ import annotations

import asyncio
import uuid

from modules.workflows.ports.channels import CallRequest, CallResult


class SimulatedTelephony:
    def __init__(self, default_digit: str = "1", delay_seconds: float = 1.0) -> None:
        self._digit = default_digit
        self._delay = delay_seconds

    async def place_keypad_call(self, request: CallRequest) -> CallResult:
        await asyncio.sleep(self._delay)
        ref = f"sim-{uuid.uuid4().hex[:10]}"
        tail = request.to[-2:]
        if tail == "00":
            return CallResult("no_answer", provider_ref=ref)
        if tail == "01":
            return CallResult("busy", provider_ref=ref)
        if tail == "02":
            return CallResult("answered", digit=None, duration_seconds=25, provider_ref=ref)
        digit = "2" if tail == "99" else self._digit
        return CallResult("answered", digit=digit, duration_seconds=18, provider_ref=ref)
