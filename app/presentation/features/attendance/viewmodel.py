"""View model coordinating filters and model data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List

from PyQt6.QtCore import QObject, pyqtSignal

from app.domain.entities.attendance_record import AttendanceRecord
from app.domain.usecases.load_attendance_records import load_attendance_records
from app.presentation.features.attendance.model import AttendanceTableModel, RowData


@dataclass(slots=True)
class FiltersState:
    text: str = ""
    date_from: date | None = None
    date_to: date | None = None


class AttendanceViewModel(QObject):
    """Binds domain data with the Qt models."""

    errorOccurred = pyqtSignal(str)
    loadingChanged = pyqtSignal(bool)

    def __init__(self, repository) -> None:
        super().__init__()
        self._repository = repository
        self._model = AttendanceTableModel()
        self._filters = FiltersState()

    @property
    def model(self) -> AttendanceTableModel:
        return self._model

    def load(self) -> None:
        self.loadingChanged.emit(True)
        try:
            rows = list(load_attendance_records(self._repository))
            filtered = self._apply_filters(rows)
            self._model.set_rows(filtered)
        except Exception as exc:  # noqa: BLE001
            self.errorOccurred.emit(str(exc))
        finally:
            self.loadingChanged.emit(False)

    def update_text_filter(self, text: str) -> None:
        self._filters.text = text.strip().lower()
        self.load()

    def update_date_range(self, date_from, date_to) -> None:
        self._filters.date_from = date_from.toPyDate() if date_from else None
        self._filters.date_to = date_to.toPyDate() if date_to else None
        self.load()

    def clear_filters(self) -> None:
        self._filters = FiltersState()
        self.load()

    def _apply_filters(self, rows: List[AttendanceRecord]) -> List[RowData]:
        filtered: List[RowData] = []
        for record in rows:
            note = (record.notes or "").lower()
            if (
                self._filters.text
                and self._filters.text not in record.employee.lower()
                and self._filters.text not in note
            ):
                continue
            if self._filters.date_from and record.date_value < self._filters.date_from:
                continue
            if self._filters.date_to and record.date_value > self._filters.date_to:
                continue
            filtered.append(
                RowData(
                    employee=record.employee,
                    date_value=record.date_value,
                    time_value=record.time_value,
                    punch_type=record.punch_type,
                    notes=record.notes,
                )
            )
        return filtered
