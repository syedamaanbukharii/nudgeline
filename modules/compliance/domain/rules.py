"""Pure rules deciding whether a call may be placed now. No I/O."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class CallingWindow:
    """Local-time hours and weekdays (0=Monday) when calls are allowed."""

    start: time = time(9, 0)
    end: time = time(21, 0)
    weekdays: frozenset[int] = field(default_factory=lambda: frozenset(range(7)))

    @classmethod
    def parse(cls, start: str, end: str, weekdays: list[int] | None = None) -> CallingWindow:
        window = cls(
            start=time.fromisoformat(start),
            end=time.fromisoformat(end),
            weekdays=frozenset(weekdays if weekdays is not None else range(7)),
        )
        if window.start >= window.end:
            raise ValueError("calling window start must be before end")
        if not window.weekdays or not window.weekdays <= frozenset(range(7)):
            raise ValueError("calling window weekdays must be a non-empty subset of 0-6")
        return window

    def contains(self, local: datetime) -> bool:
        return local.weekday() in self.weekdays and self.start <= local.time() < self.end

    def next_open(self, local: datetime) -> datetime:
        """The next moment (local time, at or after `local`) when the window is open."""
        if self.contains(local):
            return local
        day = local
        if local.weekday() in self.weekdays and local.time() < self.start:
            return day.replace(hour=self.start.hour, minute=self.start.minute, second=0, microsecond=0)
        for _ in range(8):
            day = (day + timedelta(days=1)).replace(
                hour=self.start.hour, minute=self.start.minute, second=0, microsecond=0
            )
            if day.weekday() in self.weekdays:
                return day
        raise ValueError("calling window has no open days")


@dataclass(frozen=True)
class Decision:
    """Outcome of a compliance check, stored on the run for every dial attempt."""

    allowed: bool
    reason: str
    checked_at: str
    local_time: str
    retry_at: str | None = None

    def as_dict(self) -> dict[str, str | bool | None]:
        return asdict(self)


def check_call(
    *,
    now: datetime,
    contact_timezone: str,
    window: CallingWindow,
    on_dnc_list: bool,
    attempts_made: int,
    max_attempts: int,
) -> Decision:
    """Decide whether to dial now. Order matters: hard blocks before scheduling."""
    local = now.astimezone(ZoneInfo(contact_timezone))
    stamp = {"checked_at": now.astimezone(UTC).isoformat(), "local_time": local.isoformat()}
    if on_dnc_list:
        return Decision(allowed=False, reason="dnc_list", **stamp)
    if attempts_made >= max_attempts:
        return Decision(allowed=False, reason="max_attempts", **stamp)
    if not window.contains(local):
        retry = window.next_open(local).astimezone(UTC).isoformat()
        return Decision(allowed=False, reason="outside_calling_window", retry_at=retry, **stamp)
    return Decision(allowed=True, reason="ok", **stamp)
