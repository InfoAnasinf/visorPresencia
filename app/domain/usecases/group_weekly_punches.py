"""Use case to group raw weekly punches into paired intervals by incidence."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable, List

from app.domain.entities.attendance_week import (
    DailyAttendanceSummary,
    PunchInterval,
    WeeklyPunch,
)


def group_weekly_punches(
    punches: Iterable[WeeklyPunch],
    reference: datetime | None = None,
) -> List[DailyAttendanceSummary]:
    """Group punches by day, pairing entries that share the same incidence."""
    reference = reference or datetime.now()
    day_map: dict[datetime.date, dict[int | None, List[WeeklyPunch]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for punch in sorted(punches, key=lambda p: p.timestamp):
        day_map[punch.timestamp.date()][punch.incidence].append(punch)

    summaries: List[DailyAttendanceSummary] = []
    for day in sorted(day_map):
        intervals: List[PunchInterval] = []
        total_minutes = 0
        is_working = False
        has_incomplete = False

        for incidence, entries in day_map[day].items():
            sorted_entries = sorted(entries, key=lambda p: p.timestamp)
            idx = 0
            while idx < len(sorted_entries):
                start = sorted_entries[idx]
                end = sorted_entries[idx + 1] if idx + 1 < len(sorted_entries) else None

                actual_end = _valid_end(start, end, day)
                is_active = actual_end is None and day == reference.date()
                is_incomplete = actual_end is None and day != reference.date()

                minutes = _calculate_minutes(start.timestamp, actual_end, reference, is_active)

                if minutes > 0:
                    total_minutes += minutes
                if is_active:
                    is_working = True
                if is_incomplete:
                    has_incomplete = True

                intervals.append(
                    PunchInterval(
                        incidence=incidence,
                        start=start.timestamp,
                        end=actual_end,
                        minutes=minutes,
                        is_active=is_active,
                        is_incomplete=is_incomplete,
                    )
                )

                if end is None:
                    break
                idx += 2

        intervals.sort(key=lambda interval: interval.start)
        summaries.append(
            DailyAttendanceSummary(
                day=day,
                intervals=tuple(intervals),
                total_minutes=total_minutes,
                is_working=is_working,
                has_incomplete=has_incomplete,
            )
        )

    return summaries


def _valid_end(
    start: WeeklyPunch,
    end: WeeklyPunch | None,
    day: datetime.date,
) -> datetime | None:
    """Return the end timestamp if it belongs to the same day."""
    if end is None:
        return None
    if end.timestamp.date() != day:
        return None
    if end.timestamp <= start.timestamp:
        return None
    return end.timestamp


def _calculate_minutes(
    start: datetime,
    end: datetime | None,
    reference: datetime,
    is_active: bool,
) -> int:
    """Compute minutes between start and end or current reference."""
    effective_end = reference if is_active else end
    if effective_end is None:
        return 0
    delta = effective_end - start
    minutes = int(delta.total_seconds() // 60)
    return minutes if minutes > 0 else 0
