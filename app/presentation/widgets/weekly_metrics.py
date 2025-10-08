"""Cards summarising current weekly metrics."""

from __future__ import annotations

from typing import Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel, QWidget

from app.domain.entities.weekly_metrics import WeeklyMetrics


class WeeklyMetricsWidget(QFrame):
    """Shows three key metrics for the selected employee."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("WeeklyMetrics")
        self._cards: Dict[str, QLabel] = {}
        self._build_ui()
        self.set_metrics(None)

    def _build_ui(self) -> None:
        layout = QGridLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)

        self._cards["total_hours"] = self._create_card(layout, 0, "Total horas")
        self._cards["worked_days"] = self._create_card(layout, 1, "Días trabajados")
        self._cards["incomplete"] = self._create_card(layout, 2, "Incidencias")

    def _create_card(self, layout: QGridLayout, column: int, title: str) -> QLabel:
        card = QFrame(self)
        card.setObjectName("MetricCard")
        card_layout = QGridLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(6)

        title_label = QLabel(title, card)
        title_label.setObjectName("MetricTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        value_label = QLabel("--", card)
        value_label.setObjectName("MetricValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        card_layout.addWidget(title_label, 0, 0)
        card_layout.addWidget(value_label, 1, 0)
        layout.addWidget(card, 0, column)
        return value_label

    def set_metrics(self, metrics: WeeklyMetrics | None) -> None:
        """Update displayed values."""
        if not metrics:
            self._cards["total_hours"].setText("00:00")
            self._cards["worked_days"].setText("0")
            self._cards["incomplete"].setText("0")
            return

        self._cards["total_hours"].setText(metrics.total_hours_label)
        self._cards["worked_days"].setText(str(metrics.worked_days))
        self._cards["incomplete"].setText(str(metrics.incomplete_days))
