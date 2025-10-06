"""Domain entity representing a single attendance event."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time


@dataclass(frozen=True, slots=True)
class AttendanceRecord:
    """Immutable domain representation of a punch."""

    employee: str
    date_value: date
    time_value: time
    punch_type: str
    notes: str | None = None

    @property
    def timestamp(self) -> datetime:
        """Combine date and time for easier sorting."""
        return datetime.combine(self.date_value, self.time_value)

