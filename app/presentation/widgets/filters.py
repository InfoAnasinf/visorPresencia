"""Reusable filter widgets for attendance views."""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

_SPANISH_MONTHS = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


@dataclass
class _Range:
    start: QDate
    end: QDate


class AttendanceFiltersWidget(QWidget):
    """Filter bar with week navigator and manual reload."""

    dateRangeChanged = pyqtSignal(object, object)
    reloadRequested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_range = _Range(QDate.currentDate(), QDate.currentDate())
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self._prev_button = QToolButton(self)
        self._prev_button.setObjectName("WeekNavButton")
        self._prev_button.setArrowType(Qt.ArrowType.LeftArrow)
        self._prev_button.clicked.connect(lambda: self._navigate_weeks(-1))
        layout.addWidget(self._prev_button)

        center_box = QVBoxLayout()
        center_box.setContentsMargins(0, 0, 0, 0)
        center_box.setSpacing(2)

        self._week_label = QLabel("Semana actual", self)
        self._week_label.setObjectName("WeekLabel")
        self._week_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_box.addWidget(self._week_label)

        self._range_label = QLabel("", self)
        self._range_label.setObjectName("WeekSubLabel")
        self._range_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_box.addWidget(self._range_label)

        layout.addLayout(center_box, stretch=1)

        self._next_button = QToolButton(self)
        self._next_button.setObjectName("WeekNavButton")
        self._next_button.setArrowType(Qt.ArrowType.RightArrow)
        self._next_button.clicked.connect(lambda: self._navigate_weeks(1))
        layout.addWidget(self._next_button)

        layout.addSpacing(12)

        reload_button = QPushButton("Actualizar", self)
        reload_button.setObjectName("WeekReloadButton")
        reload_button.clicked.connect(self.reloadRequested.emit)
        layout.addWidget(reload_button)

        layout.addStretch(0)

    # --- public ---------------------------------------------------------
    def set_date_range(self, start: QDate, end: QDate) -> None:
        """Programmatically update the date range."""
        self._apply_range(start, end, trigger_reload=False)

    # --- internals ------------------------------------------------------
    def _apply_range(self, start: QDate, end: QDate, *, trigger_reload: bool) -> None:
        self._current_range = _Range(start, end)
        self._update_labels()
        self.dateRangeChanged.emit(start, end)
        if trigger_reload:
            self.reloadRequested.emit()

    def _navigate_weeks(self, offset: int) -> None:
        new_start = self._current_range.start.addDays(offset * 7)
        new_end = new_start.addDays(6)
        self._apply_range(new_start, new_end, trigger_reload=True)

    def _update_labels(self) -> None:
        start = self._current_range.start
        end = self._current_range.end
        week_number, _ = start.weekNumber()
        self._week_label.setText(f"SEMANA {week_number}")
        self._range_label.setText(self._format_range(start, end))

    @staticmethod
    def _format_range(start: QDate, end: QDate) -> str:
        if start.month() == end.month():
            month = _SPANISH_MONTHS[start.month() - 1].capitalize()
            return f"{start.day():02d} – {end.day():02d} {month}"
        start_month = _SPANISH_MONTHS[start.month() - 1][:3].capitalize()
        end_month = _SPANISH_MONTHS[end.month() - 1][:3].capitalize()
        return f"{start.day():02d} {start_month} – {end.day():02d} {end_month}"
