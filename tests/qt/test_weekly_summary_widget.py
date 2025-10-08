from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QLabel

from app.presentation.widgets.weekly_summary import WeeklySummaryCarousel


def test_weekly_summary_carousel_renders_cards(qtbot):
    widget = WeeklySummaryCarousel()
    qtbot.addWidget(widget)

    cards = [
        {
            "weekday": "Lun",
            "date_label": "07/10",
            "hours_label": "08:00",
            "status": "Completado",
            "is_current": True,
            "is_incomplete": False,
        },
        {
            "weekday": "Mar",
            "date_label": "08/10",
            "hours_label": "07:15",
            "status": "Incompleto",
            "is_current": False,
            "is_incomplete": True,
        },
    ]

    widget.set_cards(cards)
    card_widgets = widget.findChildren(QFrame, "WeeklySummaryCard")
    assert len(card_widgets) == 2


def test_weekly_summary_carousel_empty_state(qtbot):
    widget = WeeklySummaryCarousel()
    qtbot.addWidget(widget)

    widget.set_empty_message("Sin fichajes")
    widget.set_cards([])

    empty_label = widget.findChild(QLabel, "WeeklySummaryEmpty")
    assert empty_label is not None
    assert empty_label.isVisible()
    assert empty_label.text() == "Sin fichajes"

