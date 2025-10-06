"""Main window hosting the attendance feature."""

from __future__ import annotations

from functools import partial

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QStatusBar, QToolBar

from app.presentation.features.attendance.viewmodel import AttendanceViewModel
from app.presentation.widgets.attendance_table import AttendanceTable
from app.presentation.widgets.filters import AttendanceFiltersWidget


class AttendanceWindow(QMainWindow):
    """Single-window shell for the attendance viewer."""

    def __init__(self, view_model: AttendanceViewModel | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Visor de Presencia")
        self.resize(1024, 640)

        # Deferred wiring: repository injection will happen during bootstrap.
        self._view_model = view_model

        self._setup_tool_bar()
        self._setup_central_widgets()
        self._setup_status_bar()

    def _setup_tool_bar(self) -> None:
        toolbar = QToolBar("Acciones", self)
        toolbar.setObjectName("MainToolBar")

        refresh_action = QAction("Recargar", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._on_refresh)
        toolbar.addAction(refresh_action)

        self.addToolBar(toolbar)

    def _setup_central_widgets(self) -> None:
        self._filters = AttendanceFiltersWidget(self)
        self._table = AttendanceTable(self)
        self.setCentralWidget(self._table)
        self.addToolBarBreak()
        self._filters_dock = self.addToolBar("Filtros")
        self._filters_dock.addWidget(self._filters)
        self._connect_filters()

    def _setup_status_bar(self) -> None:
        status = QStatusBar(self)
        self.setStatusBar(status)
        status.showMessage("Listo")

    def set_view_model(self, view_model: AttendanceViewModel) -> None:
        """Attach a view model after construction."""
        self._view_model = view_model
        self._table.setModel(view_model.model)
        self._filters.cleared.connect(view_model.clear_filters)
        self._filters.textChanged.connect(view_model.update_text_filter)
        self._filters.dateRangeChanged.connect(view_model.update_date_range)
        view_model.loadingChanged.connect(self._on_loading_changed)
        view_model.errorOccurred.connect(self.statusBar().showMessage)
        view_model.load()

    def _connect_filters(self) -> None:
        self._filters.cleared.connect(partial(self.statusBar().showMessage, "Filtros reiniciados"))

    def _on_loading_changed(self, loading: bool) -> None:
        message = "Cargando..." if loading else "Listo"
        self.statusBar().showMessage(message)
        if loading:
            QApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            QApplication.restoreOverrideCursor()

    def _on_refresh(self) -> None:
        if self._view_model:
            self._view_model.load()
