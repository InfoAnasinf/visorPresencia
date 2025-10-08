"""QTreeView configured for grouped attendance data."""

from __future__ import annotations

from PyQt6.QtWidgets import QHeaderView, QTreeView


class AttendanceTree(QTreeView):
    """Tree view with grouped rows by day."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._configure()

    def _configure(self) -> None:
        header = self.header()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setHighlightSections(False)

        self.setRootIsDecorated(True)
        self.setUniformRowHeights(True)
        self.setAlternatingRowColors(True)
        self.setIndentation(24)
        self.setExpandsOnDoubleClick(True)
        self.setAnimated(True)
        self.setAllColumnsShowFocus(True)
        self.setStyleSheet(
            """
            QTreeView {
                background: transparent;
                font-size: 13px;
                border: none;
                selection-background-color: #d8e6ff;
                selection-color: #0b3a82;
            }
            QTreeView::item {
                padding: 6px 4px;
            }
            QTreeView::item:selected {
                background-color: #d8e6ff;
                color: #0b3a82;
            }
            QTreeView::item:hover {
                background-color: #eef4ff;
            }
            QTreeView::branch:has-siblings:!adjoins-item {
                border-image: url(none);
            }
            QTreeView::branch:has-siblings:adjoins-item {
                border-image: url(none);
            }
            QTreeView::branch:!has-children:!has-siblings:adjoins-item {
                border-image: url(none);
            }
            """
        )
