from datetime import datetime

from PyQt6.QtCore import Qt

from app.presentation.features.attendance.model import AttendanceTreeModel, DayRow, IntervalRow


def test_model_reports_headers_and_hierarchy():
    day = DayRow(
        day=datetime(2025, 1, 1).date(),
        total_minutes=480,
        status="Completado",
        is_incomplete=False,
        is_current=False,
        intervals=[
            IntervalRow(
                incidence=1,
                start=datetime(2025, 1, 1, 9, 0),
                end=datetime(2025, 1, 1, 17, 0),
                duration_minutes=480,
                status="Completado",
                is_active=False,
                is_incomplete=False,
            )
        ],
    )

    model = AttendanceTreeModel([day])

    assert model.headerData(0, Qt.Orientation.Horizontal) == "Fecha"

    parent_index = model.index(0, 0)
    assert parent_index.isValid()
    assert model.data(parent_index, Qt.ItemDataRole.DisplayRole) == "Miércoles 01/01/2025"

    child_index = model.index(0, 2, parent_index)
    assert child_index.isValid()
    assert model.data(child_index, Qt.ItemDataRole.DisplayRole) == "09:00"
