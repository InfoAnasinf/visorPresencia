"""Use case responsible for building yearly attendance statistics."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Sequence

from app.data.repositories.attendance_repository import AttendanceRepository
from app.domain.entities.attendance_week import DailyAttendanceSummary, PunchInterval, WeeklyPunch
from app.domain.entities.yearly_statistics import DayLoad, YearlyStatistics
from app.domain.usecases.group_weekly_punches import group_weekly_punches

stats_logger = logging.getLogger("attendance.statistics")


def load_yearly_statistics(
    repository: AttendanceRepository,
    employee_code: str,
    year: int,
) -> YearlyStatistics:
    """Fetch punches for the requested year and compute aggregated metrics."""
    range_start = datetime(year, 1, 1, 0, 0, 0)
    range_end = datetime(year, 12, 31, 23, 59, 59, 999999)
    stats_logger.debug(
        "load_yearly_statistics: empleado=%s año=%d rango=%s -> %s",
        employee_code,
        year,
        range_start.isoformat(),
        range_end.isoformat(),
    )
    punches = (
        WeeklyPunch(timestamp=dto.timestamp, incidence=dto.incidence)
        for dto in repository.fetch_punches_between(employee_code, range_start, range_end)
    )
    summaries = group_weekly_punches(punches, reference=range_end)
    stats = build_yearly_statistics(year, summaries)
    stats_logger.debug(
        "load_yearly_statistics: completado empleado=%s año=%d total_minutos=%d dias=%d",
        employee_code,
        year,
        stats.total_minutes,
        stats.worked_days,
    )
    return stats


def build_yearly_statistics(
    year: int,
    summaries: Sequence[DailyAttendanceSummary],
) -> YearlyStatistics:
    """Aggregate the supplied daily summaries into a yearly snapshot."""
    monthly_minutes = [0 for _ in range(12)]
    weekday_minutes = [0 for _ in range(7)]
    weekday_occurrences = [0 for _ in range(7)]
    heatmap = [[0 for _ in range(24)] for _ in range(7)]

    daily_entries: list[DayLoad] = []
    total_minutes = 0
    worked_days = 0
    longest: DayLoad | None = None
    shortest: DayLoad | None = None

    for summary in summaries:
        if summary.day.year != year:
            continue
        minutes = summary.total_minutes
        if minutes <= 0:
            continue

        entry = DayLoad(day=summary.day, minutes=minutes)
        daily_entries.append(entry)
        total_minutes += minutes
        worked_days += 1

        month_index = summary.day.month - 1
        monthly_minutes[month_index] += minutes

        weekday_index = summary.day.weekday()
        weekday_minutes[weekday_index] += minutes
        weekday_occurrences[weekday_index] += 1

        if longest is None or minutes > longest.minutes:
            longest = entry
        if shortest is None or minutes < shortest.minutes:
            shortest = entry

        for interval in summary.intervals:
            if interval.end is None or interval.minutes <= 0:
                continue
            _accumulate_interval_heatmap(heatmap, interval)

    daily_entries.sort(key=lambda x: x.day)
    average = total_minutes / worked_days if worked_days else 0.0

    return YearlyStatistics(
        year=year,
        total_minutes=total_minutes,
        worked_days=worked_days,
        average_minutes_per_day=average,
        monthly_minutes=tuple(monthly_minutes),
        weekday_minutes=tuple(weekday_minutes),
        weekday_occurrences=tuple(weekday_occurrences),
        heatmap=tuple(tuple(hour for hour in row) for row in heatmap),
        daily_minutes=tuple(daily_entries),
        longest_day=longest,
        shortest_day=shortest,
    )


def _accumulate_interval_heatmap(
    heatmap: list[list[int]],
    interval: PunchInterval,
) -> None:
    """Accumulate worked minutes into a 7x24 heatmap."""
    assert interval.end is not None  # guard for mypy; filtered earlier
    current = interval.start
    end = interval.end
    while current < end:
        bucket_end = _end_of_hour(current)
        slot_end = min(bucket_end, end)
        minutes = int((slot_end - current).total_seconds() // 60)
        if minutes > 0:
            weekday = current.weekday()
            hour = current.hour
            heatmap[weekday][hour] += minutes
        current = slot_end


def _end_of_hour(timestamp: datetime) -> datetime:
    """Return the first instant of the next hour for the provided timestamp."""
    truncated = timestamp.replace(minute=0, second=0, microsecond=0)
    return truncated + timedelta(hours=1)
