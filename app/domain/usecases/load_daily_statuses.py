"""Use case retrieving daily statuses for all employees."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import List

from app.data.repositories.attendance_repository import AttendanceRepository
from app.domain.entities.employee_status import EmployeeDailyStatus


def load_daily_statuses(repository: AttendanceRepository, reference: date) -> List[EmployeeDailyStatus]:
    """Return the status of all employees for the given day."""
    statuses: List[EmployeeDailyStatus] = []
    for dto in repository.fetch_daily_statuses(reference):
        statuses.append(
            EmployeeDailyStatus(
                code=dto.code,
                display_name=dto.display_name,
                job_title=dto.job_title,
                photo=dto.photo,
                last_punch=dto.last_punch,
                punch_count=int(dto.punch_count or 0),
            )
        )
    return statuses
