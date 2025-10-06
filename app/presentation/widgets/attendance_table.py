"""QTableView configured for attendance data."""

from __future__ import annotations

from PyQt6.QtWidgets import QHeaderView, QTableView


class AttendanceTable(QTableView):
    """Pre-configured table view with high-level defaults."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._configure()

    def _configure(self) -> None:
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setWordWrap(False)

