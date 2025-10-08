from datetime import datetime

from PyQt6.QtCore import Qt

from app.domain.entities.employee_status import EmployeeDailyStatus
from app.presentation.widgets.status_table import EmployeeStatusModel


def test_employee_status_model_formats_rows():
    model = EmployeeStatusModel()
    working = EmployeeDailyStatus(
        code="001",
        display_name="Ana Perez",
        job_title="Desarrolladora",
        photo=None,
        last_punch=datetime(2025, 4, 7, 9, 30),
        punch_count=3,
    )
    absent = EmployeeDailyStatus(
        code="002",
        display_name="Luis Gomez",
        job_title=None,
        photo=None,
        last_punch=datetime(2025, 4, 7, 8, 0),
        punch_count=2,
    )
    unknown = EmployeeDailyStatus(
        code="003",
        display_name="Beatriz Soto",
        job_title="Atencion",
        photo=None,
        last_punch=None,
        punch_count=0,
    )

    model.set_statuses([unknown, working, absent])

    assert model.rowCount() == 3

    # Sorted by status order: Trabajando, Ausente, Sin datos
    assert model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole) == "Ana Perez"
    assert model.data(model.index(0, 3), Qt.ItemDataRole.DisplayRole) == "Trabajando"
    assert model.data(model.index(1, 3), Qt.ItemDataRole.DisplayRole) == "Ausente"
    assert model.data(model.index(2, 3), Qt.ItemDataRole.DisplayRole) == "Sin datos"

    # Last punch formatted
    assert model.data(model.index(0, 2), Qt.ItemDataRole.DisplayRole) == "09:30"

    # Missing job title uses dash
    assert model.data(model.index(1, 1), Qt.ItemDataRole.DisplayRole) == "-"

    # Colors applied on status column
    assert model.data(model.index(0, 3), Qt.ItemDataRole.ForegroundRole) is not None
    assert model.data(model.index(1, 3), Qt.ItemDataRole.BackgroundRole) is not None
