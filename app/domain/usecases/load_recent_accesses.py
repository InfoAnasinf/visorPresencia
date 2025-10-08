"""Use case to pull recent access events."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, List

from app.data.dto.access_event_dto import AccessEventDTO
from app.domain.entities.access_event import AccessEvent
from app.data.repositories.attendance_repository import AttendanceRepository


def load_recent_accesses(
    repository: AttendanceRepository,
    since: datetime,
    limit: int = 20,
) -> List[AccessEvent]:
    """Fetch recent access events and convert them to domain entities."""

    def _to_entity(dto: AccessEventDTO) -> AccessEvent:
        return AccessEvent(
            timestamp=dto.timestamp,
            employee_code=dto.employee_code,
            employee_name=dto.employee_name,
            badge=dto.badge,
        )

    return [_to_entity(dto) for dto in repository.fetch_recent_accesses(since, limit)]
