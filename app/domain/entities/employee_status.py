"""Domain entity representing the daily status of an employee."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class EmployeeDailyStatus:
    code: str
    display_name: str
    job_title: str | None
    photo: bytes | None
    last_punch: datetime | None
    punch_count: int

    @property
    def is_working(self) -> bool:
        """Return True when the employee appears to be clocked in."""
        return self.punch_count % 2 == 1 and self.last_punch is not None
