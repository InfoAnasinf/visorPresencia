from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.domain.entities.access_event import AccessEvent
from app.presentation.features.attendance.viewmodel import AttendanceViewModel


class DummySettings:
    def __init__(self) -> None:
        self._values: dict[str, object] = {}

    def value(self, key, default=None):
        return self._values.get(key.path(), default)

    def set_value(self, key, value) -> None:
        self._values[key.path()] = value


class DummyRepository:
    def fetch_recent_accesses(self, since, limit=20):
        return []

    def fetch_weekly_punches(self, code, week_date):
        return []

    def fetch_employees(self):
        return []

    def fetch_daily_statuses(self, reference_date):
        return []


@pytest.fixture()
def attendance_view_model(qtbot):
    vm = AttendanceViewModel(DummyRepository(), DummySettings(), enable_monitoring=False)
    qtbot.addCleanup(vm.deleteLater)
    return vm


def test_access_event_sequence_classification(attendance_view_model):
    vm = attendance_view_model
    captured: list[dict[str, object]] = []
    vm.accessEventRaised.connect(captured.append)

    base_time = datetime(2025, 10, 7, 8, 0)
    first = AccessEvent(timestamp=base_time, employee_code="001", employee_name="Ana")
    second = AccessEvent(
        timestamp=base_time + timedelta(hours=4),
        employee_code="001",
        employee_name="Ana",
    )

    vm._process_access_events([first, second])
    assert [payload["is_entry"] for payload in captured] == [True, False]

    captured.clear()
    vm._process_access_events([second])
    assert captured == []

    third = AccessEvent(
        timestamp=base_time + timedelta(days=1),
        employee_code="001",
        employee_name="Ana",
    )
    vm._process_access_events([third])
    assert captured[0]["is_entry"] is True


def test_fake_simulation_emits_events(qtbot, attendance_view_model):
    vm = attendance_view_model
    captured: list[dict[str, object]] = []
    vm.accessEventRaised.connect(captured.append)

    vm.start_fake_access_simulation(interval_ms=20)
    qtbot.waitUntil(lambda: len(captured) > 0, timeout=1000)
    vm.stop_fake_access_simulation()

    assert captured[0]["employee_code"] == "SIM001"
