"""Tree model wrapping weekly attendance grouped by day."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, List

from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt
from PyQt6.QtGui import QColor

from app.presentation.utils.i18n import spanish_weekday_name

@dataclass(slots=True)
class IntervalRow:
    incidence: int | None
    start: datetime
    end: datetime | None
    duration_minutes: int
    status: str
    is_active: bool
    is_incomplete: bool


@dataclass(slots=True)
class DayRow:
    day: date
    total_minutes: int
    status: str
    is_incomplete: bool
    is_current: bool
    intervals: List[IntervalRow]


class _Node:
    __slots__ = ("parent", "children", "payload")

    def __init__(self, payload: DayRow | IntervalRow, parent: _Node | None = None) -> None:
        self.parent = parent
        self.payload = payload
        self.children: list[_Node] = []


class AttendanceTreeModel(QAbstractItemModel):
    """Hierarchical model that displays days as groups and intervals as children."""

    headers = ["Fecha", "Incidencia", "Inicio", "Fin", "Duracion", "Estado"]

    def __init__(self, days: List[DayRow] | None = None) -> None:
        super().__init__()
        self._root = _Node(payload=None)  # type: ignore[arg-type]
        self.set_days(days or [])

    # --- Qt model overrides -------------------------------------------------
    def index(self, row: int, column: int, parent: QModelIndex | None = None) -> QModelIndex:  # noqa: N802
        parent = parent or QModelIndex()
        parent_node = self._node_from_index(parent)
        if 0 <= row < len(parent_node.children):
            child = parent_node.children[row]
            return self.createIndex(row, column, child)
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:  # noqa: N802
        if not index.isValid():
            return QModelIndex()
        node = self._node_from_index(index)
        if node.parent is None or node.parent.parent is None:
            return QModelIndex()
        grand_parent = node.parent
        row = grand_parent.parent.children.index(grand_parent)
        return self.createIndex(row, 0, grand_parent)

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        parent = parent or QModelIndex()
        node = self._node_from_index(parent)
        return len(node.children)

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        return len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:  # noqa: N802
        if not index.isValid():
            return None
        node = self._node_from_index(index)
        payload = node.payload

        if isinstance(payload, DayRow):
            if role == Qt.ItemDataRole.DisplayRole:
                return self._day_display(payload, index.column())
            if role == Qt.ItemDataRole.ForegroundRole:
                if payload.is_incomplete:
                    return QColor("#b71c1c")
                if payload.is_current and payload.status == "Trabajando":
                    return QColor("#0b5ed7")
            return None

        if isinstance(payload, IntervalRow):
            if role == Qt.ItemDataRole.DisplayRole:
                return self._interval_display(payload, index.column())
            if role == Qt.ItemDataRole.TextAlignmentRole and index.column() in (1, 2, 3, 4):
                return int(Qt.AlignmentFlag.AlignCenter)
            if role == Qt.ItemDataRole.ForegroundRole:
                if payload.is_incomplete:
                    return QColor("#b71c1c")
                if payload.is_active:
                    return QColor("#1b5e20")
            return None
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

    # --- Public API ---------------------------------------------------------
    def set_days(self, days: List[DayRow]) -> None:
        self.beginResetModel()
        self._root.children.clear()
        for day in days:
            day_node = _Node(day, parent=self._root)
            self._root.children.append(day_node)
            for interval in day.intervals:
                interval_node = _Node(interval, parent=day_node)
                day_node.children.append(interval_node)
        self.endResetModel()

    # --- Helpers ------------------------------------------------------------
    def _node_from_index(self, index: QModelIndex) -> _Node:
        if index.isValid():
            return index.internalPointer()
        return self._root

    def _day_display(self, day: DayRow, column: int) -> str:
        if column == 0:
            weekday = spanish_weekday_name(day.day, capitalize=True)
            return f"{weekday} {day.day.strftime('%d/%m/%Y')}"
        if column == 4:
            hours, minutes = divmod(day.total_minutes, 60)
            return f"{hours:02}:{minutes:02}"
        if column == 5:
            return day.status
        return ""

    def _interval_display(self, interval: IntervalRow, column: int) -> str:
        if column == 0:
            return ""
        if column == 1:
            return "" if interval.incidence is None else str(interval.incidence)
        if column == 2:
            return interval.start.strftime("%H:%M")
        if column == 3:
            if interval.end and interval.end != interval.start:
                return interval.end.strftime("%H:%M")
            return "--"
        if column == 4:
            if interval.is_incomplete:
                return "--:--"
            hours, minutes = divmod(interval.duration_minutes, 60)
            return f"{hours:02}:{minutes:02}"
        if column == 5:
            return interval.status
        return ""
