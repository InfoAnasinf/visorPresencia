from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from app.domain.entities.attendance_week import DailyAttendanceSummary, PunchInterval
from app.domain.usecases.load_yearly_statistics import build_yearly_statistics


def _interval(
    start: datetime,
    duration_minutes: int,
) -> PunchInterval:
    end = start + timedelta(minutes=duration_minutes)
    return PunchInterval(
        incidence=0,
        start=start,
        end=end,
        minutes=duration_minutes,
        is_active=False,
        is_incomplete=False,
    )


def _summary(day: date, *intervals: PunchInterval) -> DailyAttendanceSummary:
    total = sum(interval.minutes for interval in intervals)
    return DailyAttendanceSummary(
        day=day,
        intervals=tuple(intervals),
        total_minutes=total,
        is_working=False,
        has_incomplete=False,
    )


def test_build_yearly_statistics_with_multiple_days() -> None:
    year = 2025
    jan3 = _summary(
        date(year, 1, 3),
        _interval(datetime(year, 1, 3, 9, 0), 480),
    )
    feb5 = _summary(
        date(year, 2, 5),
        _interval(datetime(year, 2, 5, 8, 30), 360),
    )
    feb6 = _summary(
        date(year, 2, 6),
        _interval(datetime(year, 2, 6, 10, 0), 120),
    )

    stats = build_yearly_statistics(year, [jan3, feb5, feb6])

    assert stats.total_minutes == 480 + 360 + 120
    assert stats.worked_days == 3
    assert stats.monthly_minutes[0] == 480
    assert stats.monthly_minutes[1] == 360 + 120
    assert stats.weekday_minutes[4] == 480  # Friday
    assert stats.weekday_minutes[2] == 360  # Wednesday
    assert stats.weekday_occurrences[4] == 1
    assert stats.weekday_occurrences[3] == 1
    assert stats.longest_day and stats.longest_day.minutes == 480
    assert stats.shortest_day and stats.shortest_day.minutes == 120
    assert stats.daily_minutes[0].day == date(year, 1, 3)
    assert pytest.approx(stats.average_minutes_per_day, rel=1e-3) == (480 + 360 + 120) / 3

    # Heatmap should accumulate 60 minutes per hour slot for the long shift.
    assert stats.heatmap[4][9] == 60  # Friday at 09:00
    assert stats.heatmap[4][16] == 60  # Friday at 16:00
