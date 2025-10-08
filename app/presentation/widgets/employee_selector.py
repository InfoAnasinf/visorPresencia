"""Widgets dedicated to employee selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True, slots=True)
class EmployeeOption:
    """Represents an employee item for display and selection."""

    code: str
    display_name: str


class EmployeeSearchDialog(QDialog):
    """Dialog that lets the user search and choose an employee."""

    employeeSelected = pyqtSignal(EmployeeOption)

    def __init__(self, employees: Iterable[EmployeeOption], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Seleccionar trabajador")
        self.setObjectName("EmployeeSearchDialog")
        unique: dict[str, EmployeeOption] = {option.code: option for option in employees}
        self._employees = sorted(unique.values(), key=lambda opt: opt.display_name.lower())
        self._build_ui()
        self._populate_list(self._employees)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        self.setMinimumSize(420, 520)

        title = QLabel("Selecciona un trabajador", self)
        title.setObjectName("DialogTitle")
        layout.addWidget(title)

        self._search = QLineEdit(self)
        self._search.setPlaceholderText("Buscar por nombre...")
        self._search.setObjectName("DialogSearch")
        self._search.textChanged.connect(self._on_search_changed)
        layout.addWidget(self._search)

        self._list = QListWidget(self)
        self._list.setObjectName("DialogList")
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.itemDoubleClicked.connect(self._on_accept)
        layout.addWidget(self._list, stretch=1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.setObjectName("DialogButtons")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._apply_styles()

    def _populate_list(self, employees: Iterable[EmployeeOption]) -> None:
        self._list.clear()
        seen: set[str] = set()
        for option in employees:
            if option.code in seen:
                continue
            seen.add(option.code)
            item = QListWidgetItem(option.display_name)
            item.setData(Qt.ItemDataRole.UserRole, option)
            self._list.addItem(item)

    def _on_search_changed(self, text: str) -> None:
        text = text.strip().lower()
        if not text:
            self._populate_list(self._employees)
            return
        filtered = [option for option in self._employees if text in option.display_name.lower()]
        self._populate_list(filtered)

    def _on_accept(self) -> None:
        item = self._list.currentItem()
        if not item:
            return
        option = item.data(Qt.ItemDataRole.UserRole)
        if option:
            self.employeeSelected.emit(option)
            self.accept()

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QDialog#EmployeeSearchDialog {
                background-color: #f4f6fb;
            }
            QLabel#DialogTitle {
                font-size: 18px;
                font-weight: 600;
                color: #111827;
            }
            QLineEdit#DialogSearch {
                padding: 8px 12px;
                border-radius: 10px;
                border: 1px solid #cbd5e1;
                background-color: #ffffff;
            }
            QLineEdit#DialogSearch:focus {
                border-color: #1f6feb;
            }
            QListWidget#DialogList {
                border: 1px solid #e0e6ef;
                border-radius: 12px;
                background-color: #ffffff;
                padding: 8px;
            }
            QListWidget#DialogList::item {
                padding: 8px 6px;
                border-radius: 8px;
            }
            QListWidget#DialogList::item:selected {
                background-color: #1f6feb;
                color: #ffffff;
            }
            QDialogButtonBox#DialogButtons QPushButton {
                min-width: 90px;
                padding: 6px 12px;
                border-radius: 8px;
                font-weight: 600;
            }
            QDialogButtonBox#DialogButtons QPushButton:first-child {
                background-color: #1f6feb;
                color: #ffffff;
                border: none;
            }
            QDialogButtonBox#DialogButtons QPushButton:last-child {
                background-color: #e4e8f5;
                color: #1f2933;
                border: none;
            }
            QDialogButtonBox#DialogButtons QPushButton:first-child:hover {
                background-color: #195bc4;
            }
            """
        )


class EmployeeSelector(QWidget):
    """Compact selector with summary field and search dialog."""

    employeeChanged = pyqtSignal(EmployeeOption)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._employees: List[EmployeeOption] = []
        self._selected: EmployeeOption | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        self.setObjectName("EmployeeSelectorWidget")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self._label = QLabel("Trabajador:", self)
        self._label.setObjectName("EmployeeSelectorLabel")
        layout.addWidget(self._label)

        self._display = QLineEdit(self)
        self._display.setObjectName("EmployeeDisplay")
        self._display.setPlaceholderText("Elige a la persona a consultar")
        self._display.setReadOnly(True)
        layout.addWidget(self._display, stretch=1)

        self._search_button = QPushButton("Buscar...", self)
        self._search_button.setObjectName("EmployeeSearchButton")
        self._search_button.clicked.connect(self._open_dialog)
        layout.addWidget(self._search_button)

    def set_employees(self, employees: Iterable[EmployeeOption]) -> None:
        unique = {option.code: option for option in employees}
        self._employees = sorted(unique.values(), key=lambda opt: opt.display_name.lower())
        if self._selected and self._selected.code not in {e.code for e in self._employees}:
            self.clear_selection()

    def has_employees(self) -> bool:
        return bool(self._employees)

    def has_selection(self) -> bool:
        return self._selected is not None

    def current_code(self) -> str | None:
        return self._selected.code if self._selected else None

    def select_employee(self, code: str) -> None:
        for option in self._employees:
            if option.code == code:
                self._set_selected(option, emit=False)
                break

    def prompt_selection(self) -> None:
        self._open_dialog()

    def clear_selection(self) -> None:
        self._selected = None
        self._display.clear()

    def _open_dialog(self) -> None:
        dialog = EmployeeSearchDialog(self._employees, self)
        dialog.employeeSelected.connect(lambda option: self._set_selected(option))
        dialog.exec()

    def _set_selected(self, option: EmployeeOption, emit: bool = True) -> None:
        self._selected = option
        self._display.setText(option.display_name)
        if emit:
            self.employeeChanged.emit(option)
