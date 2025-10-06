"""Table model wrapping attendance records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from typing import Any, List

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt


@dataclass(slots=True)
class RowData:
    employee: str
    date_value: date
    time_value: time
    punch_type: str
    notes: str | None


class AttendanceTableModel(QAbstractTableModel):
    """Qt table model that exposes attendance rows."""

    headers = ["Empleado", "Fecha", "Hora", "Tipo", "Notas"]

    def __init__(self, rows: List[RowData] | None = None) -> None:
        super().__init__()
        self._rows: List[RowData] = rows or []

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent and parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent and parent.isValid():
            return 0
        return len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:  # noqa: N802
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            row = self._rows[index.row()]
            column_map = {
                0: row.employee,
                1: row.date_value.strftime("%Y-%m-%d"),
                2: row.time_value.strftime("%H:%M"),
                3: row.punch_type,
                4: row.notes or "",
            }
            return column_map.get(index.column())
        return None

    def headerData(  # noqa: N802
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return super().headerData(section, orientation, role)

    def set_rows(self, rows: List[RowData]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

