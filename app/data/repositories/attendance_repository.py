"""Attendance repository backed by SQL Server."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from sqlalchemy.orm import Session, sessionmaker

from app.data.dto.attendance_dto import AttendanceDTO


class AttendanceRepository(Protocol):
    """Repository interface for attendance records."""

    def fetch_all(self) -> Iterable[AttendanceDTO]:
        """Return all attendance rows."""


class SqlAlchemyAttendanceRepository:
    """SQLAlchemy implementation of the attendance repository."""

    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def fetch_all(self) -> Iterable[AttendanceDTO]:
        with self._session_factory() as session:
            yield from self._query_attendance(session)

    def _query_attendance(self, session: Session) -> Iterable[AttendanceDTO]:
        # TODO: Implement mapped class or text query when schema is available.
        return ()

