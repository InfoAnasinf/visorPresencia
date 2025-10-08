"""Entities representing weekly attendance information."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Tuple


@dataclass(frozen=True, slots=True)
class WeeklyPunch:
    """Single punch entry calculated from the weekly query."""

    timestamp: datetime
    incidence: int | None = None


@dataclass(frozen=True, slots=True)
class PunchInterval:
    """Represents a paired entry (entrada-salida) for a given day."""

    incidence: int | None
    start: datetime
    end: datetime | None
    minutes: int
    is_active: bool
    is_incomplete: bool


@dataclass(frozen=True, slots=True)
class DailyAttendanceSummary:
    """Aggregated data for a specific day within the week."""

    day: date
    intervals: Tuple[PunchInterval, ...] = field(default_factory=tuple)
    total_minutes: int = 0
    is_working: bool = False
    has_incomplete: bool = False
