"""Locale helpers for the presentation layer."""

from __future__ import annotations

from datetime import date

_SPANISH_WEEKDAYS = (
    "lunes",
    "martes",
    "miércoles",
    "jueves",
    "viernes",
    "sábado",
    "domingo",
)


def spanish_weekday_name(day: date, *, capitalize: bool = False) -> str:
    """Return the weekday name in Spanish for the provided date."""
    name = _SPANISH_WEEKDAYS[day.weekday()]
    return name.capitalize() if capitalize else name


def spanish_weekday_abbrev(day: date, *, capitalize: bool = False) -> str:
    """Return a three-letter abbreviation for the weekday in Spanish."""
    abbrev = spanish_weekday_name(day, capitalize=False)[:3]
    return abbrev.capitalize() if capitalize else abbrev
