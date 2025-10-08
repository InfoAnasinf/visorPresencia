from __future__ import annotations
"""Attendance repository backed by SQL Server."""


import logging

from collections.abc import Iterable
from datetime import date, datetime, time, timedelta
from typing import Protocol

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.data.dto.access_event_dto import AccessEventDTO
from app.data.dto.attendance_dto import AttendanceDTO
from app.data.dto.employee_dto import EmployeeDTO
from app.data.dto.employee_status_dto import EmployeeDailyStatusDTO
from app.data.dto.weekly_punch_dto import WeeklyPunchDTO

logger = logging.getLogger("attendance.access_monitor")
stats_logger = logging.getLogger("attendance.statistics")


class AttendanceRepository(Protocol):
    """Repository interface for attendance records."""

    def fetch_all(self) -> Iterable[AttendanceDTO]:
        """Return all attendance rows."""

    def fetch_weekly_punches(self, code: str, week_date: date) -> Iterable[WeeklyPunchDTO]:
        """Return unified punches for the week containing ``week_date``."""

    def fetch_punches_between(
        self,
        code: str,
        start: datetime,
        end: datetime,
    ) -> Iterable[WeeklyPunchDTO]:
        """Return unified punches for the given date range."""

    def fetch_employees(self) -> Iterable[EmployeeDTO]:
        """Return the employees available for selection."""

    def fetch_daily_statuses(self, reference_date: date) -> Iterable[EmployeeDailyStatusDTO]:
        """Return the last punch metadata for all employees on ``reference_date``."""

    def fetch_recent_accesses(
        self,
        since: datetime,
        limit: int = 20,
    ) -> Iterable[AccessEventDTO]:
        """Return recent entries from the access control table."""


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

    def fetch_weekly_punches(self, code: str, week_date: date) -> Iterable[WeeklyPunchDTO]:
        week_start = week_date - timedelta(days=week_date.weekday())
        week_end = week_start + timedelta(days=6)
        start_dt = datetime.combine(week_start, time.min)
        end_dt = datetime.combine(week_end, time.max)

        params = {
            "code": code,
            "week_start": start_dt,
            "week_end": end_dt,
            "company_code": "DA",
        }

        with self._session_factory() as session:
            result = session.execute(_WEEKLY_PUNCHES_SQL, params)
            for row in result.mappings():
                yield WeeklyPunchDTO(
                    timestamp=row["punch_time"],
                    incidence=row["incidence"],
                )

    def fetch_punches_between(
        self,
        code: str,
        start: datetime,
        end: datetime,
    ) -> Iterable[WeeklyPunchDTO]:
        params = {
            "code": code,
            "range_start": start,
            "range_end": end,
            "company_code": "DA",
        }
        stats_logger.debug(
            "fetch_punches_between(code=%s, start=%s, end=%s)",
            code,
            start.isoformat(),
            end.isoformat(),
        )
        with self._session_factory() as session:
            result = session.execute(_PUNCHES_BETWEEN_SQL, params)
            count = 0
            for row in result.mappings():
                count += 1
                yield WeeklyPunchDTO(
                    timestamp=row["punch_time"],
                    incidence=row["incidence"],
                )
            stats_logger.debug(
                "fetch_punches_between -> %d registros", count
            )

    def fetch_employees(self) -> Iterable[EmployeeDTO]:
        with self._session_factory() as session:
            photos: dict[str, bytes | None] = {}
            photos_result = session.execute(_EMPLOYEE_PHOTOS_SQL)
            for row in photos_result.mappings():
                photos[row["code"]] = row.get("photo")

            result = session.execute(_EMPLOYEES_SQL)
            for row in result.mappings():
                code = row["code"]
                yield EmployeeDTO(
                    code=code,
                    display_name=row["display_name"],
                    job_title=row.get("job_title"),
                    photo=photos.get(code),
                )

    def fetch_daily_statuses(self, reference_date: date) -> Iterable[EmployeeDailyStatusDTO]:
        start_dt = datetime.combine(reference_date, time.min)
        end_dt = datetime.combine(reference_date, time.max)
        params = {
            "day_start": start_dt,
            "day_end": end_dt,
            "company_code": "DA",
        }
        with self._session_factory() as session:
            result = session.execute(_DAILY_STATUS_SQL, params)
            for row in result.mappings():
                yield EmployeeDailyStatusDTO(
                    code=row["code"],
                    display_name=row["display_name"],
                    job_title=row.get("job_title"),
                    photo=row.get("photo"),
                    last_punch=row.get("last_punch"),
                    punch_count=row.get("punch_count", 0) or 0,
                )

    def fetch_recent_accesses(
        self,
        since: datetime,
        limit: int = 20,
    ) -> Iterable[AccessEventDTO]:
        params = {
            "since": since,
            "limit": limit,
            "company_code": "DA",
        }
        logger.debug("fetch_recent_accesses(since=%s, limit=%d)", since.isoformat(), limit)
        with self._session_factory() as session:
            result = session.execute(_RECENT_ACCESSES_SQL, params)
            for row in result.mappings():
                logger.debug(
                    "DB evento crudo: code=%s time=%s badge=%s",
                    row.get("code"),
                    row.get("punch_time"),
                    row.get("badge"),
                )
                yield AccessEventDTO(
                    timestamp=row["punch_time"],
                    employee_code=row["code"],
                    employee_name=row["display_name"],
                    badge=row.get("badge"),
                )


_WEEKLY_PUNCHES_SQL = text(
    """
    SELECT
        unioned.punch_time,
        unioned.incidence
    FROM (
        SELECT
            DATEADD(
                hour,
                CAST(LEFT(f.horae, 2) AS INT),
                DATEADD(minute, CAST(RIGHT(f.horae, 2) AS INT), f.fechae)
            ) AS punch_time,
            CAST(f.INCIDENCIAE AS INT) AS incidence
        FROM FICHAJES_CORRECTOS AS f
        WHERE
            f.CODIGOE = :code
            AND f.fechae BETWEEN :week_start AND :week_end

        UNION

        SELECT
            DATEADD(
                hour,
                CAST(LEFT(f.horas, 2) AS INT),
                DATEADD(minute, CAST(RIGHT(f.horas, 2) AS INT), f.fechas)
            ) AS punch_time,
            CAST(f.INCIDENCIAE AS INT) AS incidence
        FROM FICHAJES_CORRECTOS AS f
        WHERE
            f.CODIGOE = :code
            AND f.fechas BETWEEN :week_start AND :week_end

        UNION

        SELECT
            DATEADD(
                hour,
                CAST(LEFT(f.hora, 2) AS INT),
                DATEADD(minute, CAST(RIGHT(f.hora, 2) AS INT), f.fecha)
            ) AS punch_time,
            CAST(0 AS INT) AS incidence
        FROM FICHAJES AS f
        WHERE
            f.CODIGO = :code
            AND f.fecha BETWEEN :week_start AND :week_end

        UNION

        SELECT
            DATEADD(
                hour,
                t.Hora,
                DATEADD(
                    minute,
                    t.Minuto,
                    DATETIMEFROMPARTS(t.Anyo, t.Mes, t.Dia, 0, 0, 0, 0)
                )
            ) AS punch_time,
            CAST(t.CDAL AS INT) AS incidence
        FROM tbdaccesos AS t
        WHERE
            t.cba = (
                SELECT TOP (1) p.matricula
                FROM bdrrhh.dbo.personal AS p
                WHERE
                    p.codemp = :company_code
                    AND p.ano = YEAR(GETDATE())
                    AND p.codper = :code
            )
            AND DATETIMEFROMPARTS(t.Anyo, t.Mes, t.Dia, 0, 0, 0, 0)
                BETWEEN :week_start AND :week_end
    ) AS unioned
    ORDER BY unioned.punch_time
    """
)

_PUNCHES_BETWEEN_SQL = text(
    """
    SELECT
        unioned.punch_time,
        unioned.incidence
    FROM (
        SELECT
            DATEADD(
                hour,
                CAST(LEFT(f.horae, 2) AS INT),
                DATEADD(minute, CAST(RIGHT(f.horae, 2) AS INT), f.fechae)
            ) AS punch_time,
            CAST(f.INCIDENCIAE AS INT) AS incidence
        FROM FICHAJES_CORRECTOS AS f
        WHERE
            f.CODIGOE = :code
            AND f.fechae BETWEEN :range_start AND :range_end

        UNION

        SELECT
            DATEADD(
                hour,
                CAST(LEFT(f.horas, 2) AS INT),
                DATEADD(minute, CAST(RIGHT(f.horas, 2) AS INT), f.fechas)
            ) AS punch_time,
            CAST(f.INCIDENCIAE AS INT) AS incidence
        FROM FICHAJES_CORRECTOS AS f
        WHERE
            f.CODIGOE = :code
            AND f.fechas BETWEEN :range_start AND :range_end

        UNION

        SELECT
            DATEADD(
                hour,
                CAST(LEFT(f.hora, 2) AS INT),
                DATEADD(minute, CAST(RIGHT(f.hora, 2) AS INT), f.fecha)
            ) AS punch_time,
            CAST(0 AS INT) AS incidence
        FROM FICHAJES AS f
        WHERE
            f.CODIGO = :code
            AND f.fecha BETWEEN :range_start AND :range_end

        UNION

        SELECT
            DATEADD(
                hour,
                t.Hora,
                DATEADD(
                    minute,
                    t.Minuto,
                    DATETIMEFROMPARTS(t.Anyo, t.Mes, t.Dia, 0, 0, 0, 0)
                )
            ) AS punch_time,
            CAST(t.CDAL AS INT) AS incidence
        FROM tbdaccesos AS t
        WHERE
            t.cba = (
                SELECT TOP (1) p.matricula
                FROM bdrrhh.dbo.personal AS p
                WHERE
                    p.codemp = :company_code
                    AND p.ano = YEAR(GETDATE())
                    AND p.codper = :code
            )
            AND DATETIMEFROMPARTS(t.Anyo, t.Mes, t.Dia, 0, 0, 0, 0)
                BETWEEN :range_start AND :range_end
    ) AS unioned
    ORDER BY unioned.punch_time
    """
)

_EMPLOYEES_SQL = text(
    """
    SELECT
        p.codper AS code,
        CONCAT(
            LTRIM(RTRIM(ISNULL(p.NOMPER, ''))),
            ' ',
            LTRIM(RTRIM(ISNULL(p.APEL1PER, ''))),
            ' ',
            LTRIM(RTRIM(ISNULL(p.APEL2PER, '')))
        ) AS display_name,
        c.DESCRIPCION AS job_title
    FROM BDRRHH.dbo.PERSONAL AS p
    LEFT JOIN BDRRHH.dbo.CUALIFICACION AS c
        ON c.CODCLF = p.CUALIFICACION
    WHERE
        p.ANO = YEAR(GETDATE())
        AND p.FECHABAJA IS NULL
    GROUP BY
        p.codper,
        p.NOMPER,
        p.APEL1PER,
        p.APEL2PER,
        c.DESCRIPCION
    ORDER BY display_name
    """
)

_EMPLOYEE_PHOTOS_SQL = text(
    """
    SELECT
        p.codper AS code,
        p.DIBUPER AS photo
    FROM BDRRHH.dbo.PERSONAL AS p
    WHERE
        p.ANO = YEAR(GETDATE())
        AND p.FECHABAJA IS NULL
    """
)

_DAILY_STATUS_SQL = text(
    """
    WITH base AS (
        SELECT
            code,
            display_name,
            job_title,
            photo
        FROM (
            SELECT
                p.codper AS code,
                CONCAT(
                    LTRIM(RTRIM(ISNULL(p.NOMPER, ''))),
                    ' ',
                    LTRIM(RTRIM(ISNULL(p.APEL1PER, ''))),
                    ' ',
                    LTRIM(RTRIM(ISNULL(p.APEL2PER, '')))
                ) AS display_name,
                c.DESCRIPCION AS job_title,
                p.DIBUPER AS photo,
                ROW_NUMBER() OVER (
                    PARTITION BY p.codper
                    ORDER BY p.ANO DESC, p.codper
                ) AS rn
            FROM BDRRHH.dbo.PERSONAL AS p
            LEFT JOIN BDRRHH.dbo.CUALIFICACION AS c
                ON c.CODCLF = p.CUALIFICACION
            WHERE
                p.ANO = YEAR(GETDATE())
                AND p.FECHABAJA IS NULL
        ) AS ranked
        WHERE ranked.rn = 1
    ),
    punch_events AS (
        SELECT
            raw.code,
            raw.punch_time
        FROM (
            SELECT
                f.CODIGO AS code,
                DATEADD(
                    hour,
                    CAST(LEFT(f.hora, 2) AS INT),
                    DATEADD(minute, CAST(RIGHT(f.hora, 2) AS INT), f.fecha)
                ) AS punch_time
            FROM FICHAJES AS f
            WHERE
                f.fecha BETWEEN :day_start AND :day_end

            UNION

            SELECT
                f.CODIGOE AS code,
                DATEADD(
                    hour,
                    CAST(LEFT(f.horae, 2) AS INT),
                    DATEADD(minute, CAST(RIGHT(f.horae, 2) AS INT), f.fechae)
                ) AS punch_time
            FROM FICHAJES_CORRECTOS AS f
            WHERE
                f.fechae BETWEEN :day_start AND :day_end

            UNION

            SELECT
                f.CODIGOE AS code,
                DATEADD(
                    hour,
                    CAST(LEFT(f.horas, 2) AS INT),
                    DATEADD(minute, CAST(RIGHT(f.horas, 2) AS INT), f.fechas)
                ) AS punch_time
            FROM FICHAJES_CORRECTOS AS f
            WHERE
                f.fechas BETWEEN :day_start AND :day_end

            UNION

            SELECT
                p.codper AS code,
                DATEADD(
                    hour,
                    t.Hora,
                    DATEADD(
                        minute,
                        t.Minuto,
                        DATETIMEFROMPARTS(t.Anyo, t.Mes, t.Dia, 0, 0, 0, 0)
                    )
                ) AS punch_time
            FROM tbdaccesos AS t
            INNER JOIN BDRRHH.dbo.PERSONAL AS p
                ON p.matricula = t.cba
            WHERE
                p.codemp = :company_code
                AND DATETIMEFROMPARTS(t.Anyo, t.Mes, t.Dia, 0, 0, 0, 0)
                    BETWEEN :day_start AND :day_end
        ) AS raw
        GROUP BY raw.code, raw.punch_time
    ),
    aggregated AS (
        SELECT
            pe.code,
            MAX(pe.punch_time) AS last_punch,
            COUNT(*) AS punch_count
        FROM punch_events AS pe
        GROUP BY pe.code
    )
    SELECT
        base.code,
        base.display_name,
        base.job_title,
        base.photo,
        aggregated.last_punch,
        ISNULL(aggregated.punch_count, 0) AS punch_count
    FROM base
    LEFT JOIN aggregated
        ON aggregated.code = base.code
    ORDER BY base.display_name
    """
)

_RECENT_ACCESSES_SQL = text(
    """
    WITH source AS (
        SELECT
            DATETIMEFROMPARTS(t.Anyo, t.Mes, t.Dia, t.Hora, t.Minuto, 0, 0) AS punch_time,
            p.codper AS code,
            CONCAT(
                LTRIM(RTRIM(ISNULL(p.NOMPER, ''))),
                ' ',
                LTRIM(RTRIM(ISNULL(p.APEL1PER, ''))),
                ' ',
                LTRIM(RTRIM(ISNULL(p.APEL2PER, '')))
            ) AS display_name,
            t.cba AS badge
        FROM tbdaccesos AS t
        INNER JOIN BDRRHH.dbo.PERSONAL AS p
            ON p.matricula = t.cba
        WHERE
            p.codemp = :company_code and p.ANO = YEAR(GETDATE())
    )
    SELECT
        source.punch_time,
        source.code,
        source.display_name,
        source.badge
    FROM source
    WHERE source.punch_time > :since
    ORDER BY source.punch_time ASC
    OFFSET 0 ROWS FETCH NEXT :limit ROWS ONLY
    """
)
