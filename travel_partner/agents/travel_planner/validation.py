"""Validation of model output and privacy screening of user text."""

from __future__ import annotations

import re

from pydantic import ValidationError

from .schemas import Itinerary

_CARD_CANDIDATE = re.compile(r"\b(?:\d[ -]?){13,19}\b")
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_PASSPORT_NUMBER = re.compile(r"\b(passport)(\s*(?:number|no\.?|#)?\s*(?:is|:)?\s*)([A-Z0-9]{6,9})\b", re.IGNORECASE)
_SECRET_KEY = re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{8,}")
_IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}\b")

REDACTED = "[removed]"


def _luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def redact_sensitive(text: str) -> tuple[str, bool]:
    """Strip card numbers, SSNs, passport numbers, IBANs and API keys.

    Returns the cleaned text and whether anything was removed. Dates and
    phone-like numbers that fail the Luhn check are left alone.
    """
    changed = False

    def card(match: re.Match[str]) -> str:
        nonlocal changed
        digits = re.sub(r"\D", "", match.group(0))
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            changed = True
            return REDACTED
        return match.group(0)

    out = _CARD_CANDIDATE.sub(card, text)
    for pattern in (_SSN, _IBAN, _SECRET_KEY):
        out, n = pattern.subn(REDACTED, out)
        changed = changed or n > 0

    def passport(match: re.Match[str]) -> str:
        nonlocal changed
        # Only redact when the token contains a digit; "passport is French" is fine.
        if not any(c.isdigit() for c in match.group(3)):
            return match.group(0)
        changed = True
        return f"{match.group(1)}{match.group(2)}{REDACTED}"

    out = _PASSPORT_NUMBER.sub(passport, out)
    return out, changed


class ItineraryValidationError(ValueError):
    """Raised with a short, model-readable explanation of what is wrong."""


def validate_itinerary(data: object) -> Itinerary:
    try:
        itinerary = Itinerary.model_validate(data)
    except ValidationError as exc:
        problems = "; ".join(f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in exc.errors()[:10])
        raise ItineraryValidationError(problems) from None

    numbers = [d.day_number for d in itinerary.days]
    if numbers != list(range(1, len(numbers) + 1)):
        raise ItineraryValidationError("days must be numbered 1, 2, 3, ... in order")
    if len(itinerary.days) != itinerary.duration_days:
        raise ItineraryValidationError(
            f"duration_days is {itinerary.duration_days} but {len(itinerary.days)} days were given"
        )
    return itinerary
