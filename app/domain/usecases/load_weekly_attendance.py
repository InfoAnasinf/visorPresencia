"""Use case to fetch and prepare weekly attendance intervals."""

from __future__ import annotations

from datetime import date, datetime
from typing import List

from app.data.repositories.attendance_repository import AttendanceRepository
from app.domain.entities.attendance_week import DailyAttendanceSummary, WeeklyPunch
from app.domain.usecases.group_weekly_punches import group_weekly_punches


def load_weekly_attendance(
    repository: AttendanceRepository,
    employee_code: str,
    week_start: date,
    reference: datetime | None = None,
) -> List[DailyAttendanceSummary]:
    """Fetch the weekly punches and transform them into paired intervals."""
    reference = reference or datetime.now()
    punches = (
        WeeklyPunch(timestamp=dto.timestamp, incidence=dto.incidence)
        for dto in repository.fetch_weekly_punches(employee_code, week_start)
    )
    return group_weekly_punches(punches, reference=reference)
