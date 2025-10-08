"""Use case to load employees available for selection."""

from __future__ import annotations

from collections.abc import Iterable
from typing import List

from app.data.repositories.attendance_repository import AttendanceRepository
from app.domain.entities.employee import Employee


def load_employees(repository: AttendanceRepository) -> List[Employee]:
    """Fetch employees from repository and map to domain entities."""
    seen: dict[str, Employee] = {}
    for dto in repository.fetch_employees():
        job_title = dto.job_title.strip() if dto.job_title else None
        employee = Employee(
            code=dto.code,
            display_name=dto.display_name.strip(),
            job_title=job_title,
            photo=dto.photo,
        )
        seen[employee.code] = employee
    return list(seen.values())
