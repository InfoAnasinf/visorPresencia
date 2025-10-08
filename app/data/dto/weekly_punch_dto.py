"""DTO representing the unified weekly punches query result."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class WeeklyPunchDTO:
    """Raw punch data with the calculated timestamp and optional incidence."""

    timestamp: datetime
    incidence: int | None

