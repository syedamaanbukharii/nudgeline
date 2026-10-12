"""Country defaults for new tenants and for choosing a call language."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Region:
    timezone: str
    currency: str
    arabic: bool


REGIONS: dict[str, Region] = {
    "AE": Region("Asia/Dubai", "AED", True),
    "SA": Region("Asia/Riyadh", "SAR", True),
    "QA": Region("Asia/Qatar", "QAR", True),
    "KW": Region("Asia/Kuwait", "KWD", True),
    "BH": Region("Asia/Bahrain", "BHD", True),
    "OM": Region("Asia/Muscat", "OMR", True),
    "EG": Region("Africa/Cairo", "EGP", True),
    "JO": Region("Asia/Amman", "JOD", True),
    "IN": Region("Asia/Kolkata", "INR", False),
    "PK": Region("Asia/Karachi", "PKR", False),
    "GB": Region("Europe/London", "GBP", False),
    "US": Region("America/New_York", "USD", False),
}

DEFAULT_COUNTRY = "AE"


def region_for(country: str) -> Region:
    return REGIONS.get(country.upper(), REGIONS[DEFAULT_COUNTRY])


def is_arabic_speaking(country: str | None) -> bool:
    return bool(country) and REGIONS.get((country or "").upper(), Region("", "", False)).arabic
