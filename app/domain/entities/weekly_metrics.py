"""Value object summarising attendance metrics for a week."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WeeklyMetrics:
    total_minutes: int
    incomplete_days: int
    worked_days: int

    @property
    def total_hours_label(self) -> str:
        hours, minutes = divmod(self.total_minutes, 60)
        return f"{hours:02}:{minutes:02}"
