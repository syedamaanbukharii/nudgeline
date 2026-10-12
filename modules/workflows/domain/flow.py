"""Pure workflow logic: language choice, script rendering and the next-step decision."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Literal

from modules.compliance.domain.rules import Decision, check_call
from modules.tenancy.domain.regions import is_arabic_speaking

if TYPE_CHECKING:
    from modules.workflows.domain.settings import WorkflowSettings

TERMINAL = frozenset({"confirmed", "cancelled", "no_response", "blocked", "failed", "skipped"})

_CURRENCY_WORDS: dict[str, tuple[str, str]] = {
    "AED": ("درهم", "dirhams"),
    "SAR": ("ريال", "riyals"),
    "QAR": ("ريال قطري", "riyals"),
    "KWD": ("دينار كويتي", "dinars"),
    "BHD": ("دينار بحريني", "dinars"),
    "OMR": ("ريال عماني", "rials"),
    "EGP": ("جنيه", "pounds"),
    "JOD": ("دينار", "dinars"),
    "INR": ("روبية", "rupees"),
    "PKR": ("روبية", "rupees"),
    "USD": ("دولار", "dollars"),
    "GBP": ("جنيه إسترليني", "pounds"),
}


def choose_language(preference: str | None, workflow_default: str, phone_country: str | None) -> str:
    """Customer locale wins, then the workflow setting, then the phone's country."""
    if preference:
        code = preference.lower()[:2]
        if code in ("ar", "en"):
            return code
    if workflow_default in ("ar", "en"):
        return workflow_default
    return "ar" if is_arabic_speaking(phone_country) else "en"


def spoken_amount(total: str | None) -> str:
    if not total:
        return ""
    try:
        value = Decimal(total)
    except InvalidOperation:
        return total
    return str(value.quantize(Decimal(1))) if value == value.to_integral_value() else f"{value:.2f}"


def currency_words(code: str | None, language: str) -> str:
    if not code:
        return ""
    words = _CURRENCY_WORDS.get(code.upper())
    if words is None:
        return code.upper()
    return words[0] if language == "ar" else words[1]


def render(text: str, values: dict[str, str]) -> str:
    """Fill {placeholders}; unknown placeholders become empty, never raw braces."""
    rendered = re.sub(r"\{(\w+)\}", lambda m: values.get(m.group(1), ""), text)
    return re.sub(r"\s{2,}", " ", rendered).strip()


@dataclass(frozen=True)
class RunState:
    whatsapp_sent_at: datetime | None
    call_attempts: int
    on_dnc_list: bool
    contact_timezone: str


@dataclass(frozen=True)
class Step:
    kind: Literal["send_whatsapp", "place_call", "wait", "finish"]
    until: datetime | None = None
    outcome: str | None = None
    reason: str | None = None
    decision: Decision | None = None


def next_step(
    state: RunState,
    settings: WorkflowSettings,
    now: datetime,
    *,
    whatsapp_available: bool,
    telephony_available: bool,
) -> Step:
    use_whatsapp = settings.whatsapp.enabled and whatsapp_available
    use_call = settings.call.enabled and telephony_available

    if state.on_dnc_list:
        return Step("finish", outcome="blocked", reason="dnc_list")

    if use_whatsapp:
        if state.whatsapp_sent_at is None:
            return Step("send_whatsapp")
        reply_deadline = state.whatsapp_sent_at + timedelta(minutes=settings.whatsapp.wait_minutes)
        if now < reply_deadline:
            return Step("wait", until=reply_deadline, reason="awaiting_whatsapp_reply")

    if use_call:
        decision = check_call(
            now=now,
            contact_timezone=state.contact_timezone,
            window=settings.window.to_rule(),
            on_dnc_list=False,
            attempts_made=state.call_attempts,
            max_attempts=settings.call.max_attempts,
        )
        if decision.allowed:
            return Step("place_call", decision=decision)
        if decision.reason == "outside_calling_window" and decision.retry_at:
            return Step(
                "wait", until=datetime.fromisoformat(decision.retry_at), reason=decision.reason, decision=decision
            )
        return Step("finish", outcome="no_response", reason=decision.reason, decision=decision)

    if use_whatsapp:
        return Step("finish", outcome="no_response", reason="no_whatsapp_reply")
    return Step("finish", outcome="failed", reason="no_channel_configured")


def after_failed_call(attempts_made: int, settings: WorkflowSettings, now: datetime) -> Step:
    """No usable answer on this attempt: retry later or give up."""
    if attempts_made >= settings.call.max_attempts:
        return Step("finish", outcome="no_response", reason="max_attempts")
    return Step("wait", until=now + timedelta(minutes=settings.call.retry_minutes), reason="retry_call")
