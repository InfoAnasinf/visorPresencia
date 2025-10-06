"""Use case for loading attendance records from a repository."""

from __future__ import annotations

from collections.abc import Iterable

from app.data.repositories.attendance_repository import AttendanceRepository
from app.domain.entities.attendance_record import AttendanceRecord


def load_attendance_records(repository: AttendanceRepository) -> Iterable[AttendanceRecord]:
    """Load data from the repository and map to domain entities."""
    for dto in repository.fetch_all():
        yield AttendanceRecord(
            employee=dto.employee,
            date_value=dto.date_value,
            time_value=dto.time_value,
            punch_type=dto.punch_type,
            notes=dto.notes,
        )

