"""Domain entity representing a realtime access event."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class AccessEvent:
    """Single badge punch coming from the access control table."""

    timestamp: datetime
    employee_code: str
    employee_name: str
    badge: str | None = None
