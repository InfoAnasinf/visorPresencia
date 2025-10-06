"""DTO definition for attendance records at the persistence layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time


@dataclass(slots=True)
class AttendanceDTO:
    """Represents a persisted punch row."""

    employee: str
    date_value: date
    time_value: time
    punch_type: str
    notes: str | None = None

