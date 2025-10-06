"""Reusable filter widgets for attendance views."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)


class AttendanceFiltersWidget(QWidget):
    """Compound widget exposing filter signals to the view model."""

    textChanged = pyqtSignal(str)
    dateRangeChanged = pyqtSignal(object, object)
    cleared = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("Buscar empleado o nota")
        self.search_edit.textChanged.connect(self.textChanged)

        self.from_edit = QDateEdit(self)
        self.from_edit.setCalendarPopup(True)
        self.to_edit = QDateEdit(self)
        self.to_edit.setCalendarPopup(True)

        self.from_edit.dateChanged.connect(self._on_date_changed)
        self.to_edit.dateChanged.connect(self._on_date_changed)

        clear_button = QPushButton("Limpiar", self)
        clear_button.clicked.connect(self.cleared)

        layout.addWidget(QLabel("Buscar:", self))
        layout.addWidget(self.search_edit, stretch=2)
        layout.addWidget(QLabel("Desde:", self))
        layout.addWidget(self.from_edit)
        layout.addWidget(QLabel("Hasta:", self))
        layout.addWidget(self.to_edit)
        layout.addWidget(clear_button)

    def _on_date_changed(self) -> None:
        self.dateRangeChanged.emit(self.from_edit.date(), self.to_edit.date())

