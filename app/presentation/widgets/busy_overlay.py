"""Translucent overlay showing a busy indicator while loading."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class BusyIndicator(QWidget):
    """Simple spinner composed of animated spokes."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._step = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self.setFixedSize(56, 56)

    def start(self) -> None:
        if not self._timer.isActive():
            self._timer.start(80)

    def stop(self) -> None:
        self._timer.stop()
        self._step = 0
        self.update()

    def _advance(self) -> None:
        self._step = (self._step + 1) % 12
        self.update()

    def paintEvent(self, event) -> None:  # noqa: D401
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        radius = min(self.width(), self.height()) / 2 - 4
        painter.translate(self.rect().center())

        base_color = QColor("#1f6feb")
        for i in range(12):
            painter.save()
            painter.rotate(30 * i)
            factor = ((i + self._step) % 12) / 12
            color = QColor(base_color)
            color.setAlphaF(0.25 + 0.75 * (1 - factor))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(radius * 0.4, -4, radius * 0.3, 8, 4, 4)
            painter.restore()


class BusyOverlay(QFrame):
    """Overlay that blocks interaction and shows a spinner."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("BusyOverlay")
        self.setVisible(False)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._indicator = BusyIndicator(self)
        layout.addWidget(self._indicator, 0, Qt.AlignmentFlag.AlignCenter)

        self._label = QLabel("Cargando datos...", self)
        self._label.setObjectName("BusyLabel")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label, 0, Qt.AlignmentFlag.AlignCenter)

    def show_overlay(self, message: str | None = None) -> None:
        if message:
            self._label.setText(message)
        else:
            self._label.setText("Cargando datos...")
        self._indicator.start()
        self.raise_()
        self.setVisible(True)

    def hide_overlay(self) -> None:
        self._indicator.stop()
        self.setVisible(False)
