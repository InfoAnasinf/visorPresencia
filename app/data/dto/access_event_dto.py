"""Data transfer object for access events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class AccessEventDTO:
    timestamp: datetime
    employee_code: str
    employee_name: str
    badge: str | None
