"""Compact header showing selected employee details."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.domain.entities.employee import Employee


class EmployeeHeader(QFrame):
    """Header bar displaying employee identity and quick actions."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("EmployeeHeader")
        self._employee: Optional[Employee] = None
        self._build_ui()
        self._render_placeholder()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        self._avatar = QLabel(self)
        self._avatar.setObjectName("EmployeeAvatar")
        self._avatar.setFixedSize(72, 72)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._avatar)

        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)

        self._name_label = QLabel("Selecciona un trabajador", self)
        self._name_label.setObjectName("EmployeeName")
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self._role_label = QLabel("", self)
        self._role_label.setObjectName("EmployeeRole")
        self._role_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        info_layout.addWidget(self._name_label)
        info_layout.addWidget(self._role_label)
        layout.addLayout(info_layout, stretch=1)

        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        self._mail_button = QToolButton(self)
        self._mail_button.setObjectName("EmployeeMailAction")
        self._mail_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation))
        self._mail_button.setToolTip("Enviar email (proximamente)")
        self._mail_button.setEnabled(False)
        actions_layout.addWidget(self._mail_button)

        self._contact_button = QToolButton(self)
        self._contact_button.setObjectName("EmployeeContactAction")
        self._contact_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogYesButton))
        self._contact_button.setToolTip("Contactar (proximamente)")
        self._contact_button.setEnabled(False)
        actions_layout.addWidget(self._contact_button)

        layout.addLayout(actions_layout)

    def set_employee(self, employee: Employee | None) -> None:
        """Display identity for the given employee."""
        self._employee = employee
        if not employee:
            self._render_placeholder()
            return
        self._name_label.setText(employee.display_name or "Trabajador sin nombre")
        role = employee.job_title or "Puesto no asignado"
        self._role_label.setText(role)
        self._render_photo(employee)

    # --- helpers ---------------------------------------------------------
    def _render_placeholder(self) -> None:
        self._avatar.setProperty("hasPhoto", False)
        self._avatar.setPixmap(QPixmap())
        self._avatar.setText("--")
        self._name_label.setText("Selecciona un trabajador")
        self._role_label.setText("Ningun trabajador seleccionado")

    def _render_photo(self, employee: Employee) -> None:
        pixmap = QPixmap()
        if employee.photo and pixmap.loadFromData(employee.photo):
            pixmap = pixmap.scaled(
                self._avatar.width(),
                self._avatar.height(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._avatar.setPixmap(pixmap)
            self._avatar.setProperty("hasPhoto", True)
        else:
            initials = self._initials(employee.display_name)
            self._avatar.setPixmap(QPixmap())
            self._avatar.setText(initials)
            self._avatar.setProperty("hasPhoto", False)
        self._avatar.style().unpolish(self._avatar)
        self._avatar.style().polish(self._avatar)

    @staticmethod
    def _initials(display_name: str) -> str:
        parts = [segment for segment in display_name.strip().split() if segment]
        if not parts:
            return "--"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()
