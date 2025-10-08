"""Entities describing yearly statistics for an employee."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Tuple


@dataclass(frozen=True, slots=True)
class DayLoad:
    """Represents the total minutes worked for a specific day."""

    day: date
    minutes: int


def _default_monthly_minutes() -> Tuple[int, ...]:
    return tuple(0 for _ in range(12))


def _default_weekday_minutes() -> Tuple[int, ...]:
    return tuple(0 for _ in range(7))


def _default_weekday_occurrences() -> Tuple[int, ...]:
    return tuple(0 for _ in range(7))


def _default_heatmap() -> Tuple[Tuple[int, ...], ...]:
    return tuple(tuple(0 for _ in range(24)) for _ in range(7))


@dataclass(frozen=True, slots=True)
class YearlyStatistics:
    """Aggregated working patterns for a calendar year."""

    year: int
    total_minutes: int
    worked_days: int
    average_minutes_per_day: float
    monthly_minutes: Tuple[int, ...] = field(default_factory=_default_monthly_minutes)
    weekday_minutes: Tuple[int, ...] = field(default_factory=_default_weekday_minutes)
    weekday_occurrences: Tuple[int, ...] = field(default_factory=_default_weekday_occurrences)
    heatmap: Tuple[Tuple[int, ...], ...] = field(default_factory=_default_heatmap)
    daily_minutes: Tuple[DayLoad, ...] = field(default_factory=tuple)
    longest_day: DayLoad | None = None
    shortest_day: DayLoad | None = None
