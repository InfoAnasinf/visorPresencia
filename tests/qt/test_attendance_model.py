from datetime import date, time

from PyQt6.QtCore import Qt

from app.presentation.features.attendance.model import AttendanceTableModel, RowData


def test_model_reports_headers():
    model = AttendanceTableModel(
        [
            RowData(
                employee="Ana",
                date_value=date(2025, 1, 1),
                time_value=time(9, 0),
                punch_type="entrada",
                notes=None,
            )
        ]
    )

    assert model.headerData(0, Qt.Orientation.Horizontal) == "Empleado"
