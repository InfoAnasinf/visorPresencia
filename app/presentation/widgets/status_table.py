"""Widgets to display daily employee statuses."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Sequence

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QHeaderView, QTableView, QWidget

from app.domain.entities.employee_status import EmployeeDailyStatus


@dataclass(slots=True)
class EmployeeStatusRow:
    code: str
    name: str
    job_title: str | None
    last_punch: datetime | None
    status_label: str
    status_color: QColor
    status_background: QColor


class EmployeeStatusModel(QAbstractTableModel):
    """Table model exposing the status of each employee for today."""

    headers = ["Empleado", "Puesto", "Último fichaje", "Estado"]

    STATUS_ORDER = {"Trabajando": 0, "Ausente": 1, "Sin datos": 2}

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: List[EmployeeStatusRow] = []
        self._index_by_code: Dict[str, int] = {}

    # --- Qt overrides ----------------------------------------------------
    def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        return len(self._rows)

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        return len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):  # noqa: N802, ANN001
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if column == 0:
                return row.name
            if column == 1:
                return row.job_title or "-"
            if column == 2:
                return row.last_punch.strftime("%H:%M") if row.last_punch else "--:--"
            if column == 3:
                return row.status_label

        if role == Qt.ItemDataRole.ForegroundRole and column == 3:
            return row.status_color

        if role == Qt.ItemDataRole.BackgroundRole and column == 3:
            return row.status_background

        if role == Qt.ItemDataRole.TextAlignmentRole and column in (2, 3):
            return int(Qt.AlignmentFlag.AlignCenter)

        return None

    def headerData(  # noqa: N802
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return super().headerData(section, orientation, role)

    # --- Public API ------------------------------------------------------
    def set_statuses(self, statuses: Sequence[EmployeeDailyStatus]) -> None:
        """Replace the table contents."""
        self.beginResetModel()
        converted = [self._convert(status) for status in statuses]
        self._rows = sorted(
            converted,
            key=lambda row: (self.STATUS_ORDER.get(row.status_label, 99), row.name.lower()),
        )
        self._index_by_code = {row.code: idx for idx, row in enumerate(self._rows)}
        self.endResetModel()

    def _convert(self, status: EmployeeDailyStatus) -> EmployeeStatusRow:
        label, color, background = self._status_palette(status)
        return EmployeeStatusRow(
            code=status.code,
            name=status.display_name,
            job_title=status.job_title,
            last_punch=status.last_punch,
            status_label=label,
            status_color=color,
            status_background=background,
        )

    # --- helpers ---------------------------------------------------------
    def code_at(self, row: int) -> Optional[str]:
        if 0 <= row < len(self._rows):
            return self._rows[row].code
        return None

    def row_for_code(self, code: str) -> Optional[int]:
        return self._index_by_code.get(code)

    @staticmethod
    def _status_palette(status: EmployeeDailyStatus) -> tuple[str, QColor, QColor]:
        if status.is_working:
            foreground = QColor("#0f8a4d")
            background = QColor(foreground)
            background.setAlpha(28)
            return "Trabajando", foreground, background
        if status.last_punch is None:
            foreground = QColor("#5f6c80")
            background = QColor(foreground)
            background.setAlpha(16)
            return "Sin datos", foreground, background
        foreground = QColor("#b42318")
        background = QColor(foreground)
        background.setAlpha(20)
        return "Ausente", foreground, background

class EmployeeStatusTable(QTableView):
    """Configured table view for the status model."""

    employeeSelected = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("EmployeeStatusTable")
        self._model = EmployeeStatusModel(self)
        self.setModel(self._model)
        self._suppress_selection = False
        self._configure()
        self.selectionModel().currentRowChanged.connect(self._on_current_row_changed)

    def _configure(self) -> None:
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setHighlightSections(False)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet(
            """
            QTableView#EmployeeStatusTable {
                background: transparent;
                font-size: 13px;
            }
            QTableView#EmployeeStatusTable::item {
                padding: 6px 4px;
            }
            QTableView#EmployeeStatusTable::item:selected {
                background-color: #d8e6ff;
                color: #0b3a82;
            }
            QTableView#EmployeeStatusTable::item:hover {
                background-color: #eef4ff;
            }
            """
        )

    def set_statuses(self, statuses: Sequence[EmployeeDailyStatus]) -> None:
        self._model.set_statuses(statuses)

    def select_employee(self, code: str) -> None:
        row = self._model.row_for_code(code)
        if row is None:
            return
        if self.selectionModel() is None:
            return
        self._suppress_selection = True
        self.clearSelection()
        self.selectRow(row)
        self._suppress_selection = False

    # --- handlers --------------------------------------------------------
    def _on_current_row_changed(self, current: QModelIndex, previous: QModelIndex) -> None:
        if self._suppress_selection or not current.isValid():
            return
        code = self._model.code_at(current.row())
        if code:
            self.employeeSelected.emit(code)
