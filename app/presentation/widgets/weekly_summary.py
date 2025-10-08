"""Horizontal carousel showing weekly punches per day."""

from __future__ import annotations

from typing import Iterable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class WeeklySummaryCarousel(QFrame):
    """Scrollable set of day cards for the current week."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("WeeklySummaryCarousel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._scroll = QScrollArea(self)
        self._scroll.setObjectName("WeeklySummaryScroll")
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setWidgetResizable(True)

        self._container = QWidget(self._scroll)
        self._container.setObjectName("WeeklySummaryContainer")
        self._cards_layout = QHBoxLayout(self._container)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(12)
        self._tail_spacer: QSpacerItem | None = None

        self._scroll.setWidget(self._container)
        layout.addWidget(self._scroll)

        self._empty_label = QLabel("", self)
        self._empty_label.setObjectName("WeeklySummaryEmpty")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setVisible(False)
        layout.addWidget(self._empty_label)

    def set_cards(self, cards: Iterable[dict[str, object]]) -> None:
        """Populate the carousel with the provided day summaries."""
        items = list(cards)
        self._clear_cards()
        if not items:
            self._scroll.setVisible(False)
            self._empty_label.setVisible(True)
            return

        self._scroll.setVisible(True)
        self._empty_label.setVisible(False)
        for data in items:
            self._cards_layout.addWidget(self._create_card(data))
        self._ensure_tail_spacer()

    # --- helpers ---------------------------------------------------------
    def set_empty_message(self, message: str) -> None:
        """Update the placeholder message displayed when there are no cards."""
        self._empty_label.setText(message)

    def _clear_cards(self) -> None:
        if self._tail_spacer:
            self._cards_layout.removeItem(self._tail_spacer)
            self._tail_spacer = None
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _ensure_tail_spacer(self) -> None:
        self._tail_spacer = QSpacerItem(
            0,
            0,
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
        self._cards_layout.addItem(self._tail_spacer)

    def _create_card(self, data: dict[str, object]) -> QWidget:
        card = QFrame(self._container)
        card.setObjectName("WeeklySummaryCard")
        card.setProperty("state", str(data.get("status", "")).lower())
        card.setProperty("isCurrent", "true" if data.get("is_current") else "false")
        card.setProperty("isIncomplete", "true" if data.get("is_incomplete") else "false")
        card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        card.setFixedWidth(152)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        weekday = QLabel(f"{data.get('weekday', '')} {data.get('date_label', '')}", card)
        weekday.setObjectName("WeeklySummaryWeekday")
        weekday.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        hours = QLabel(str(data.get("hours_label", "--:--")), card)
        hours.setObjectName("WeeklySummaryHours")
        hours.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        status_label = QLabel(str(data.get("status", "")), card)
        status_label.setObjectName("WeeklySummaryStatus")
        status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(weekday)
        layout.addWidget(hours)
        layout.addWidget(status_label)
        layout.addStretch(1)
        return card
