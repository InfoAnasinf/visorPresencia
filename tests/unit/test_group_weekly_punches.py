from datetime import datetime, timedelta

from app.domain.entities.attendance_week import WeeklyPunch
from app.domain.usecases.group_weekly_punches import group_weekly_punches


def test_group_weekly_punches_pairs_by_incidence_and_marks_active():
    monday = datetime(2025, 2, 3, 9, 0)
    monday_exit = monday.replace(hour=17)
    tuesday = datetime(2025, 2, 4, 9, 30)
    sunday = datetime(2025, 2, 2, 8, 0)  # previous day, missing exit
    reference = tuesday.replace(hour=17, minute=30)

    punches = [
        WeeklyPunch(timestamp=monday, incidence=1),
        WeeklyPunch(timestamp=monday_exit, incidence=1),
        WeeklyPunch(timestamp=tuesday, incidence=2),
        WeeklyPunch(timestamp=sunday, incidence=3),
    ]

    summaries = group_weekly_punches(punches, reference=reference)

    assert len(summaries) == 3

    sunday_summary = summaries[0]
    assert sunday_summary.has_incomplete is True
    sunday_interval = sunday_summary.intervals[0]
    assert sunday_interval.is_incomplete is True
    assert sunday_interval.minutes == 0

    monday_summary = summaries[1]
    assert monday_summary.total_minutes == 480
    assert monday_summary.is_working is False
    first_interval = monday_summary.intervals[0]
    assert first_interval.incidence == 1
    assert first_interval.is_active is False
    assert first_interval.is_incomplete is False
    assert first_interval.minutes == 480

    tuesday_summary = summaries[2]
    assert tuesday_summary.is_working is True
    active_interval = tuesday_summary.intervals[0]
    assert active_interval.incidence == 2
    assert active_interval.is_active is True
    assert active_interval.is_incomplete is False
    assert active_interval.end is None
    assert active_interval.minutes == 480  # from 09:30 to 17:30
