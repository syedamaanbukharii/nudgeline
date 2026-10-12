"""Workflow templates. Each industry use case is a template over the same engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

LANGUAGES = ("ar", "en")


@dataclass(frozen=True)
class KeypadOption:
    digit: str
    outcome: str
    label: dict[str, str]


@dataclass(frozen=True)
class Template:
    key: str
    name: dict[str, str]
    description: dict[str, str]
    industry: str
    variables: tuple[str, ...]
    options: tuple[KeypadOption, ...]
    script: dict[str, dict[str, str]]
    available: bool = True

    def outcome_for_digit(self, digit: str | None) -> str | None:
        return next((o.outcome for o in self.options if o.digit == digit), None)

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "industry": self.industry,
            "variables": list(self.variables),
            "options": [{"digit": o.digit, "outcome": o.outcome, "label": o.label} for o in self.options],
            "script": self.script,
            "available": self.available,
        }


ORDER_CONFIRMATION = Template(
    key="order_confirmation",
    name={"en": "Order confirmation (COD)", "ar": "تأكيد الطلب (الدفع عند الاستلام)"},
    description={
        "en": "Call every new cash-on-delivery order. Press 1 to confirm, 2 to cancel.",
        "ar": "اتصال بكل طلب جديد بالدفع عند الاستلام. اضغط 1 للتأكيد و2 للإلغاء.",
    },
    industry="ecommerce",
    variables=("customer_name", "store_name", "order_number", "total", "currency", "items"),
    options=(
        KeypadOption("1", "confirmed", {"en": "Confirm", "ar": "تأكيد"}),
        KeypadOption("2", "cancelled", {"en": "Cancel", "ar": "إلغاء"}),
    ),
    script={
        "en": {
            "prompt": (
                "Hello {customer_name}. This is an automated call from {store_name} about your order "
                "{order_number} for {total} {currency}. Press 1 to confirm your order. Press 2 to cancel it."
            ),
            "confirmed": "Thank you. Your order is confirmed.",
            "cancelled": "Your order has been cancelled. Thank you.",
            "no_input": "We did not receive your choice. We will try again later. Goodbye.",
        },
        "ar": {
            "prompt": (
                "مرحباً {customer_name}. هذه مكالمة آلية من {store_name} بخصوص طلبك رقم {order_number} "
                "بقيمة {total} {currency}. لتأكيد الطلب اضغط واحد. لإلغاء الطلب اضغط اثنين."
            ),
            "confirmed": "شكراً لك. تم تأكيد طلبك.",
            "cancelled": "تم إلغاء طلبك. شكراً لك.",
            "no_input": "لم نستلم اختيارك. سنحاول مرة أخرى لاحقاً. مع السلامة.",
        },
    },
)

APPOINTMENT_CONFIRMATION = Template(
    key="appointment_confirmation",
    name={"en": "Appointment confirmation", "ar": "تأكيد الموعد"},
    description={
        "en": "Clinics and salons: confirm or cancel tomorrow's appointments.",
        "ar": "للعيادات والصالونات: تأكيد أو إلغاء مواعيد الغد.",
    },
    industry="healthcare",
    variables=("customer_name", "store_name", "order_number"),
    options=(
        KeypadOption("1", "confirmed", {"en": "Confirm", "ar": "تأكيد"}),
        KeypadOption("2", "cancelled", {"en": "Cancel", "ar": "إلغاء"}),
    ),
    script={"en": {}, "ar": {}},
    available=False,
)

TEMPLATES: dict[str, Template] = {t.key: t for t in (ORDER_CONFIRMATION, APPOINTMENT_CONFIRMATION)}


def get_template(key: str) -> Template:
    template = TEMPLATES.get(key)
    if template is None or not template.available:
        raise KeyError(key)
    return template
