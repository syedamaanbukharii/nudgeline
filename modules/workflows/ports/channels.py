"""Ports the engine uses to reach customers and stores. Adapters live in other modules."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Literal, Protocol


@dataclass(frozen=True)
class CallRequest:
    run_id: uuid.UUID
    to: str
    language: str
    prompt: str
    replies: dict[str, str]
    digits: dict[str, str]
    repeat_prompt: int = 2
    input_timeout_seconds: int = 8


@dataclass(frozen=True)
class CallResult:
    status: Literal["answered", "no_answer", "busy", "failed"]
    digit: str | None = None
    duration_seconds: int | None = None
    provider_ref: str | None = None
    error: str | None = None


class TelephonyPort(Protocol):
    async def place_keypad_call(self, request: CallRequest) -> CallResult: ...


@dataclass(frozen=True)
class WhatsAppRequest:
    run_id: uuid.UUID
    to: str
    language: str
    template_name: str
    parameters: list[str]
    button_payloads: list[str] = field(default_factory=list)


class WhatsAppPort(Protocol):
    async def send_template(self, request: WhatsAppRequest) -> str:
        """Send a pre-approved template message; returns the provider message id."""
        ...


@dataclass(frozen=True)
class OutcomeEvent:
    run_id: uuid.UUID
    source: str
    external_ref: str
    order_number: str
    outcome: str
    channel: str | None
    tag: str | None
    cancel_order: bool


class OutcomeSink(Protocol):
    async def apply(self, event: OutcomeEvent) -> None:
        """Write the outcome back to wherever the order came from (store, callback URL)."""
        ...


@dataclass
class Channels:
    telephony: TelephonyPort | None = None
    whatsapp: WhatsAppPort | None = None
    outcome_sinks: dict[str, OutcomeSink] = field(default_factory=dict)
