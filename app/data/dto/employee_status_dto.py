"""DTO holding per-employee daily status data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class EmployeeDailyStatusDTO:
    code: str
    display_name: str
    job_title: str | None
    photo: bytes | None
    last_punch: datetime | None
    punch_count: int
