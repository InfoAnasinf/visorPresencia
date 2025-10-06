from datetime import date, time
from unittest.mock import MagicMock

from app.domain.usecases.load_attendance_records import load_attendance_records


def test_load_flow_maps_repository_dtos():
    dto = MagicMock(
        employee="Ana",
        date_value=date(2025, 1, 1),
        time_value=time(9, 0),
        punch_type="entrada",
        notes=None,
    )
    repository = MagicMock()
    repository.fetch_all.return_value = [dto]

    results = list(load_attendance_records(repository))

    assert results[0].employee == "Ana"
