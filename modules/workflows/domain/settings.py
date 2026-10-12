"""Validated workflow settings and script content."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from modules.compliance.domain.rules import CallingWindow


class WhatsAppStep(BaseModel):
    enabled: bool = False
    template_name: str = "order_confirmation"
    wait_minutes: int = Field(default=15, ge=1, le=720)


class CallStep(BaseModel):
    enabled: bool = True
    max_attempts: int = Field(default=3, ge=1, le=6)
    retry_minutes: int = Field(default=30, ge=5, le=1440)
    repeat_prompt: int = Field(default=2, ge=1, le=3)
    input_timeout_seconds: int = Field(default=8, ge=3, le=20)


class Window(BaseModel):
    start: str = "09:00"
    end: str = "21:00"
    weekdays: list[int] = Field(default_factory=lambda: list(range(7)))

    @model_validator(mode="after")
    def _check(self) -> Window:
        CallingWindow.parse(self.start, self.end, self.weekdays)
        return self

    def to_rule(self) -> CallingWindow:
        return CallingWindow.parse(self.start, self.end, self.weekdays)


class OutcomeAction(BaseModel):
    tag: str | None = None
    cancel_order: bool = False

    @field_validator("tag")
    @classmethod
    def _tag(cls, v: str | None) -> str | None:
        if v is not None and not re.fullmatch(r"[\w\- ]{1,40}", v):
            raise ValueError("tags may use letters, numbers, spaces, - and _ (max 40)")
        return v or None


class Actions(BaseModel):
    confirmed: OutcomeAction = OutcomeAction(tag="cod-confirmed")
    cancelled: OutcomeAction = OutcomeAction(tag="cod-cancelled", cancel_order=False)
    no_response: OutcomeAction = OutcomeAction(tag="cod-no-response")


class WorkflowSettings(BaseModel):
    delay_minutes: int = Field(default=0, ge=0, le=1440)
    cod_only: bool = True
    whatsapp: WhatsAppStep = WhatsAppStep()
    call: CallStep = CallStep()
    window: Window = Window()
    actions: Actions = Actions()

    @model_validator(mode="after")
    def _one_channel(self) -> WorkflowSettings:
        if not self.whatsapp.enabled and not self.call.enabled:
            raise ValueError("enable at least one channel: WhatsApp or call")
        return self


Language = Literal["auto", "ar", "en"]

SCRIPT_KEYS = ("prompt", "confirmed", "cancelled", "no_input")


class LanguageScript(BaseModel):
    prompt: str = Field(min_length=10, max_length=600)
    confirmed: str = Field(min_length=2, max_length=300)
    cancelled: str = Field(min_length=2, max_length=300)
    no_input: str = Field(min_length=2, max_length=300)


class Script(BaseModel):
    ar: LanguageScript
    en: LanguageScript
