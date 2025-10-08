from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest
from PyQt6.QtWidgets import QLabel, QPushButton

from app.domain.entities.attendance_week import DailyAttendanceSummary, PunchInterval
from app.domain.entities.yearly_statistics import YearlyStatistics
from app.domain.usecases.load_yearly_statistics import build_yearly_statistics
from app.presentation.widgets.yearly_statistics import YearlyStatisticsTab


def _interval(start: datetime, minutes: int) -> PunchInterval:
    end = start + timedelta(minutes=minutes)
    return PunchInterval(
        incidence=0,
        start=start,
        end=end,
        minutes=minutes,
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


@pytest.fixture
def sample_stats() -> YearlyStatistics:
    year = 2025
    jan3 = _summary(date(year, 1, 3), _interval(datetime(year, 1, 3, 9, 0), 480))
    feb5 = _summary(date(year, 2, 5), _interval(datetime(year, 2, 5, 8, 30), 360))
    feb6 = _summary(date(year, 2, 6), _interval(datetime(year, 2, 6, 10, 0), 120))
    return build_yearly_statistics(year, [jan3, feb5, feb6])


def test_statistics_tab_transitions_through_states(qtbot, sample_stats) -> None:
    widget = YearlyStatisticsTab()
    qtbot.addWidget(widget)

    widget.set_employee_available(True)
    generate_button = widget.findChild(QPushButton, "YearlyStatsGenerateButton")
    assert generate_button.isEnabled()

    widget.set_loading(2025)
    assert not generate_button.isEnabled()

    widget.set_statistics(sample_stats)
    assert generate_button.isEnabled()
    assert widget._summary_labels["total_hours"].text() == "16:00"
    assert widget._summary_labels["top_day"].text().startswith("03/01")

    heatmap_item = widget._heatmap_table.item(4, 9)  # Friday 09:00
    assert heatmap_item.text() == "01:00"

    widget.clear()
    message_label = widget.findChild(QLabel, "YearlyStatsMessage")
    assert message_label.isVisible()
