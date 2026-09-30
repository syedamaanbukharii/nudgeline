"""Structured logging configuration with PII redaction."""

from __future__ import annotations

import logging
import re
import sys

import structlog

# Patterns for PII redaction
_PII_PATTERNS = [
    (re.compile(r'"?(?:phone|mobile|tel)["\s:=]+["\s]*([+]?\d[\d\s\-().]{6,18}\d)'), "[REDACTED_PHONE]"),
    (re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"), "[REDACTED_EMAIL]"),
    (re.compile(r"(?:Bearer|Basic)\s+[A-Za-z0-9\-._~+/]+=*"), "[REDACTED_TOKEN]"),
    (re.compile(r'(?:Authorization|X-Api-Key)["\s:=]+\S+'), "[REDACTED_AUTH]"),
]


def redact_pii(_, __, event_dict: dict) -> dict:
    """Redact PII from log events."""
    message = event_dict.get("event", "")
    if isinstance(message, str):
        for pattern, replacement in _PII_PATTERNS:
            message = pattern.sub(replacement, message)
        event_dict["event"] = message
    return event_dict


def configure_logging(json_output: bool = True) -> None:
    """Configure structlog for JSON output with PII redaction."""
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        redact_pii,  # type: ignore
    ]

    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
