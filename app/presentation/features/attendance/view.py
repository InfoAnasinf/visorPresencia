"""Main window hosting the attendance feature."""

from __future__ import annotations

from PyQt6.QtCore import QDate, QEvent, Qt
from PyQt6.QtGui import QAction, QColor, QCloseEvent, QCursor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QMenu,
    QSizePolicy,
    QStatusBar,
    QSystemTrayIcon,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.domain.entities.yearly_statistics import YearlyStatistics
from app.presentation.features.attendance.viewmodel import AttendanceViewModel
from app.presentation.widgets.attendance_table import AttendanceTree
from app.presentation.widgets.employee_header import EmployeeHeader
from app.presentation.widgets.filters import AttendanceFiltersWidget
from app.presentation.widgets.busy_overlay import BusyOverlay
from app.presentation.widgets.status_table import EmployeeStatusTable
from app.presentation.widgets.weekly_metrics import WeeklyMetricsWidget
from app.presentation.widgets.weekly_summary import WeeklySummaryCarousel
from app.presentation.widgets.yearly_statistics import YearlyStatisticsTab


class AttendanceWindow(QMainWindow):
    """Single-window shell for the attendance viewer."""

    def __init__(self, view_model: AttendanceViewModel | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Visor de Presencia")
        self.resize(1024, 640)
        self._tray_icon: QSystemTrayIcon | None = None
        self._toast_icons: dict[str, QIcon] = {}
        self._allow_close = False
        self._tray_hint_shown = False
        self._simulate_action: QAction | None = None
        self._reset_seen_action: QAction | None = None

        # Deferred wiring: repository injection will happen during bootstrap.
        self._view_model = view_model

        self._setup_tray_icon()
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

        toolbar.addSeparator()
        self._simulate_action = QAction("Simular fichajes", self)
        self._simulate_action.setCheckable(True)
        self._simulate_action.setIcon(self._create_colored_icon("#f59e0b"))
        self._simulate_action.toggled.connect(self._on_toggle_simulation)
        toolbar.addAction(self._simulate_action)

        self._reset_seen_action = QAction("Reiniciar toasts", self)
        self._reset_seen_action.setIcon(self._create_colored_icon("#0ea5e9"))
        self._reset_seen_action.triggered.connect(self._on_reset_seen_events)
        toolbar.addAction(self._reset_seen_action)

        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

    def _setup_central_widgets(self) -> None:
        container = QWidget(self)
        container.setObjectName("MainContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        self._employee_header = EmployeeHeader(container)
        layout.addWidget(self._employee_header)

        self._current_employee_code: str | None = None

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(18)
        layout.addLayout(content_layout, stretch=1)

        left_panel = self._build_left_panel(container)
        right_panel = self._build_right_panel(container)
        content_layout.addWidget(left_panel, stretch=1)
        content_layout.addWidget(right_panel, stretch=1)

        self.setCentralWidget(container)
        self._apply_styles()
        self._busy_overlay = BusyOverlay(container)
        self._update_overlay_geometry()

    def _build_left_panel(self, parent: QWidget) -> QFrame:
        panel = QFrame(parent)
        panel.setObjectName("LeftPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        section_title = QLabel("FICHAJES SEMANALES", panel)
        section_title.setObjectName("WeeklySectionTitle")
        section_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(section_title)

        self._summary_card = QFrame(panel)
        self._summary_card.setObjectName("SummaryCard")
        summary_layout = QVBoxLayout(self._summary_card)
        summary_layout.setContentsMargins(16, 14, 16, 14)
        summary_layout.setSpacing(12)
        summary_header = QLabel("Semana en curso", self._summary_card)
        summary_header.setObjectName("SummaryHeader")
        self._summary_carousel = WeeklySummaryCarousel(self._summary_card)
        self._summary_carousel.set_empty_message("Selecciona un trabajador para comenzar.")
        self._summary_carousel.set_cards([])
        summary_layout.addWidget(summary_header)
        summary_layout.addWidget(self._summary_carousel)
        layout.addWidget(self._summary_card)

        self._metrics_widget = WeeklyMetricsWidget(panel)
        layout.addWidget(self._metrics_widget)

        filters_card = QFrame(panel)
        filters_card.setObjectName("FiltersCard")
        filters_layout = QVBoxLayout(filters_card)
        filters_layout.setContentsMargins(12, 12, 12, 12)
        filters_layout.setSpacing(10)
        filters_title = QLabel("Rango de fechas", filters_card)
        filters_title.setObjectName("FiltersTitle")
        self._filters = AttendanceFiltersWidget(filters_card)
        filters_layout.addWidget(filters_title)
        filters_layout.addWidget(self._filters)
        layout.addWidget(filters_card)

        table_card = QFrame(panel)
        table_card.setObjectName("TableCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)
        self._table = AttendanceTree(table_card)
        self._table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        table_layout.addWidget(self._table)
        layout.addWidget(table_card, stretch=1)
        return panel

    def _build_right_panel(self, parent: QWidget) -> QFrame:
        panel = QFrame(parent)
        panel.setObjectName("RightPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        tabs = QTabWidget(panel)
        tabs.setObjectName("StatusTabs")
        layout.addWidget(tabs, stretch=1)

        status_tab = QWidget(tabs)
        status_layout = QVBoxLayout(status_tab)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(12)

        title = QLabel("Situación del equipo", status_tab)
        title.setObjectName("StatusTitle")
        status_layout.addWidget(title)

        self._status_table = EmployeeStatusTable(status_tab)
        status_layout.addWidget(self._status_table, stretch=1)
        tabs.addTab(status_tab, "Situación")

        self._stats_tab = YearlyStatisticsTab(tabs)
        tabs.addTab(self._stats_tab, "Estadísticas")

        self._status_tabs = tabs
        return panel

    def _setup_status_bar(self) -> None:
        status = QStatusBar(self)
        self.setStatusBar(status)
        status.showMessage("Listo")

    def _setup_tray_icon(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self._tray_icon = None
            self._allow_close = True
            self._toast_icons = {}
            return
        base_icon = self._create_colored_icon("#4361ee")
        self._tray_icon = QSystemTrayIcon(base_icon, self)
        self.setWindowIcon(base_icon)
        menu = QMenu(self)
        show_action = QAction("Mostrar visor", self)
        exit_action = QAction("Salir", self)
        show_action.triggered.connect(self._restore_from_tray)
        exit_action.triggered.connect(self._quit_from_tray)
        menu.addAction(show_action)
        menu.addAction(exit_action)
        self._tray_icon.setContextMenu(menu)
        self._tray_icon.activated.connect(self._on_tray_activated)
        self._tray_icon.show()
        self._toast_icons = {
            "entry": self._create_colored_icon("#bfead2"),
            "exit": self._create_colored_icon("#ffe0b2"),
            "default": base_icon,
        }

    def set_view_model(self, view_model: AttendanceViewModel) -> None:
        """Attach a view model after construction."""
        self._view_model = view_model
        self._table.setModel(view_model.model)
        self._filters.dateRangeChanged.connect(view_model.update_date_range)
        self._filters.reloadRequested.connect(self._on_reload_requested)
        self._status_table.employeeSelected.connect(self._on_status_employee_selected)
        self._stats_tab.generateRequested.connect(self._on_yearly_stats_requested)
        view_model.employeesLoaded.connect(self._on_employees_loaded)
        view_model.employeeSelectionChanged.connect(self._on_employee_selected_from_model)
        view_model.weeklySummaryReady.connect(self._on_weekly_summary)
        view_model.employeeCardReady.connect(self._employee_header.set_employee)
        view_model.weeklyMetricsReady.connect(self._metrics_widget.set_metrics)
        view_model.dailyStatusesReady.connect(self._on_daily_statuses)
        view_model.accessEventRaised.connect(self._on_access_event)
        view_model.loadingChanged.connect(self._on_loading_changed)
        view_model.errorOccurred.connect(self._on_error)
        view_model.yearlyStatisticsLoading.connect(self._on_yearly_stats_loading)
        view_model.yearlyStatisticsReady.connect(self._on_yearly_stats_ready)
        view_model.yearlyStatisticsFailed.connect(self._on_yearly_stats_failed)
        view_model.yearlyStatisticsCleared.connect(self._on_yearly_stats_cleared)
        self._set_default_week()
        view_model.initialize()

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget#MainContainer {
                background-color: #f4f6fb;
            }
            QFrame#EmployeeHeader {
                background-color: #ffffff;
                border-radius: 16px;
                border: 1px solid #e0e6ef;
            }
            QLabel#EmployeeAvatar {
                background-color: #dbe7ff;
                border-radius: 36px;
                color: #1f3c88;
                font-weight: 600;
                font-size: 18px;
            }
            QLabel#EmployeeAvatar[hasPhoto="true"] {
                background-color: transparent;
            }
            QLabel#EmployeeName {
                font-size: 20px;
                font-weight: 600;
                color: #111827;
            }
            QLabel#EmployeeRole {
                font-size: 13px;
                color: #475467;
            }
            QLabel#WeeklySectionTitle {
                font-size: 18px;
                font-weight: 700;
                color: #102347;
                letter-spacing: 0.08em;
            }
            QToolButton#EmployeeMailAction,
            QToolButton#EmployeeContactAction {
                background-color: #eff4ff;
                border-radius: 8px;
                padding: 6px;
            }
            QFrame#LeftPanel,
            QFrame#RightPanel {
                background-color: #ffffff;
                border-radius: 16px;
                border: 1px solid #e0e6ef;
            }
            QFrame#SummaryCard {
                background-color: #f5f9ff;
                border-radius: 12px;
            }
            QLabel#SummaryHeader {
                color: #1f3c88;
                font-size: 12px;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                font-weight: 600;
            }
            QFrame#WeeklySummaryCarousel {
                border: none;
            }
            QLabel#WeeklySummaryEmpty {
                color: #475467;
                font-size: 13px;
                padding: 4px 0;
            }
            QFrame#WeeklySummaryCard {
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid #dce4f5;
            }
            QFrame#WeeklySummaryCard[state="trabajando"] {
                background-color: #e9f2ff;
                border-color: #bcd3ff;
            }
            QFrame#WeeklySummaryCard[state="incompleto"] {
                background-color: #fff4eb;
                border-color: #f59e0b;
            }
            QFrame#WeeklySummaryCard[state="completado"] {
                background-color: #f4fbf5;
                border-color: #bbf7d0;
            }
            QFrame#WeeklySummaryCard[isCurrent="true"] {
                border-width: 2px;
            }
            QLabel#WeeklySummaryWeekday {
                font-size: 12px;
                font-weight: 600;
                color: #1f2933;
                letter-spacing: 0.02em;
            }
            QLabel#WeeklySummaryHours {
                font-size: 24px;
                font-weight: 700;
                color: #0f172a;
            }
            QLabel#WeeklySummaryStatus {
                font-size: 12px;
                color: #475467;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            QFrame#WeeklyMetrics {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e0e6ef;
            }
            QFrame#MetricCard {
                background-color: #f8fafc;
                border-radius: 10px;
            }
            QLabel#MetricTitle {
                font-size: 12px;
                color: #475467;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            QLabel#MetricValue {
                font-size: 20px;
                font-weight: 600;
                color: #111827;
            }
            QFrame#FiltersCard {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e0e6ef;
            }
            QLabel#FiltersTitle {
                font-weight: 600;
                color: #1f2933;
                font-size: 14px;
            }
            QLabel#StatusTitle {
                font-size: 16px;
                font-weight: 600;
                color: #111827;
            }
            QTabWidget#StatusTabs::pane {
                border: none;
            }
            QTabBar::tab {
                background-color: #f1f5f9;
                border: 1px solid #e0e6ef;
                border-bottom: none;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                padding: 8px 16px;
                color: #475467;
                margin-right: 6px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #1f2933;
                font-weight: 600;
            }
            QFrame#YearlyStatsControls {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e0e6ef;
                padding: 12px 16px;
            }
            QLabel#YearlyStatsMessage,
            QLabel#YearlyStatsLoadingLabel {
                color: #475467;
                font-size: 14px;
            }
            QLabel#YearlyStatsErrorLabel {
                color: #b91c1c;
            }
            QFrame#YearlyStatsSummaryFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e0e6ef;
            }
            QFrame#YearlySummaryCard {
                background-color: #f8fafc;
                border-radius: 12px;
            }
            QLabel#YearlySummaryTitle {
                color: #64748b;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            QLabel#YearlySummaryValue {
                color: #0f172a;
                font-size: 20px;
                font-weight: 600;
            }
            QFrame#YearlyStatsChartFrame,
            QFrame#YearlyStatsHeatmapFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e0e6ef;
            }
            QLabel#YearlyStatsChartTitle {
                font-size: 15px;
                font-weight: 600;
                color: #1f2933;
            }
            QLabel#YearlyStatsHeatmapLegend {
                color: #475467;
                font-size: 12px;
            }
            QTableWidget#YearlyStatsHeatmap {
                gridline-color: rgba(148, 163, 184, 40%);
                selection-background-color: transparent;
            }
            QToolButton#WeekNavButton {
                background-color: #eef2ff;
                border: 1px solid #d1dcff;
                border-radius: 12px;
                padding: 6px;
                color: #1f3c88;
            }
            QToolButton#WeekNavButton:hover {
                background-color: #dfe8ff;
            }
            QLabel#WeekLabel {
                font-size: 14px;
                font-weight: 700;
                color: #0b1f4f;
                text-transform: uppercase;
            }
            QLabel#WeekSubLabel {
                font-size: 12px;
                color: #475467;
            }
            QPushButton#WeekReloadButton {
                background-color: #1f6feb;
                border-radius: 10px;
                padding: 6px 20px;
                color: #ffffff;
                font-weight: 600;
            }
            QPushButton#WeekReloadButton:hover {
                background-color: #195bc4;
            }
            QToolBar#MainToolBar {
                background: #ffffff;
                border: none;
                padding: 8px 16px;
            }
            QToolBar#MainToolBar QToolButton {
                background-color: #1f6feb;
                color: #ffffff;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QToolBar#MainToolBar QToolButton:hover {
                background-color: #195bc4;
            }
            QTreeView {
                border: none;
                selection-background-color: #d8e6ff;
                selection-color: #0b3a82;
                gridline-color: #e1e5ee;
                alternate-background-color: #f9fbff;
            }
            QTreeView::item:hover {
                background-color: #eef4ff;
            }
            QHeaderView::section {
                background-color: #f0f3fa;
                padding: 8px;
                border: none;
                font-weight: 600;
            }
            QFrame#BusyOverlay {
                background-color: rgba(244, 246, 251, 0.86);
                border-radius: 24px;
            }
            QLabel#BusyLabel {
                color: #1f2933;
                font-size: 14px;
                font-weight: 600;
            }
            """
        )

    def _create_colored_icon(self, color_hex: str) -> QIcon:
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color_hex))
        painter.drawEllipse(6, 6, 36, 36)
        painter.end()
        return QIcon(pixmap)

    def _restore_from_tray(self) -> None:
        self._allow_close = False
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quit_from_tray(self) -> None:
        self._allow_close = True
        if self._tray_icon:
            self._tray_icon.hide()
        self.close()
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._restore_from_tray()

    def changeEvent(self, event: QEvent) -> None:  # noqa: D401
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange and self.isMinimized():
            event.accept()
            self.hide()
            self._notify_tray_running()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: D401
        if self._tray_icon and not self._allow_close:
            event.ignore()
            self.hide()
            self._notify_tray_running()
            return
        super().closeEvent(event)

    def _notify_tray_running(self) -> None:
        if not self._tray_icon or self._tray_hint_shown:
            return
        icon = self._toast_icons.get("default")
        if icon:
            self._tray_icon.showMessage(
                "Visor de Presencia",
                "La aplicacion sigue activa en la bandeja del sistema.",
                icon,
                2000,
            )
        else:
            self._tray_icon.showMessage(
                "Visor de Presencia",
                "La aplicacion sigue activa en la bandeja del sistema.",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )
        self._tray_hint_shown = True

    def _on_access_event(self, payload: dict[str, object]) -> None:
        if not self._tray_icon:
            return
        icon = self._toast_icons.get("entry" if payload.get("is_entry") else "exit")
        timestamp = payload.get("timestamp")
        time_label = timestamp.strftime("%H:%M") if hasattr(timestamp, "strftime") else ""
        employee = str(payload.get("employee_name", ""))
        badge = payload.get("badge")
        parts = [part for part in (employee, time_label, badge) if part]
        message = " - ".join(parts) if parts else "Nuevo fichaje"
        title = "Entrada registrada" if payload.get("is_entry") else "Salida registrada"
        toast_icon = icon or self._toast_icons.get("default")
        if toast_icon:
            self._tray_icon.showMessage(title, message, toast_icon, 3000)
        else:
            self._tray_icon.showMessage(
                title,
                message,
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )

    def _on_loading_changed(self, loading: bool) -> None:
        if loading:
            self.statusBar().showMessage("Cargando...")
            QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
            self._update_overlay_geometry()
            self._busy_overlay.show_overlay("Cargando fichajes...")
        else:
            QApplication.restoreOverrideCursor()
            self._busy_overlay.hide_overlay()

    def _on_toggle_simulation(self, checked: bool) -> None:
        if not self._view_model:
            if self._simulate_action:
                self._simulate_action.blockSignals(True)
                self._simulate_action.setChecked(False)
                self._simulate_action.blockSignals(False)
            self.statusBar().showMessage("Inicializa el visor antes de simular fichajes.")
            return
        if checked:
            self._view_model.start_fake_access_simulation()
            self.statusBar().showMessage("Simulación de fichajes demo activa.")
        else:
            self._view_model.stop_fake_access_simulation()
            self.statusBar().showMessage("Simulación de fichajes detenida.")

    def _on_reset_seen_events(self) -> None:
        if not self._view_model:
            self.statusBar().showMessage("Inicializa el visor antes de reiniciar avisos.")
            return
        self._view_model.reset_seen_events()
        self.statusBar().showMessage("Se reinició la detección de fichajes recientes.")

    def _on_refresh(self) -> None:
        if not self._view_model:
            return
        if not self._view_model.has_employees():
            self._view_model.reload_employees()
            return
        if not self._view_model.has_selected_employee():
            self.statusBar().showMessage("Selecciona un trabajador en la lista de situacion.")
            return
        self._view_model.load()

    def _on_reload_requested(self) -> None:
        if not self._view_model:
            return
        if not self._view_model.has_selected_employee():
            self.statusBar().showMessage("Selecciona un trabajador en la lista de situacion.")
            return
        self.statusBar().showMessage("Recuperando fichajes...")
        self._view_model.load()

    def _on_status_employee_selected(self, code: str) -> None:
        if not self._view_model:
            return
        if self._current_employee_code == code:
            return
        self._view_model.select_employee(code)

    def _on_employees_loaded(self, employees: list) -> None:
        if not employees:
            self.statusBar().showMessage("No se encontraron trabajadores activos.")
            self._employee_header.set_employee(None)
            self._stats_tab.set_employee_available(False)
        else:
            self.statusBar().showMessage(f"{len(employees)} trabajadores disponibles.")
            self._stats_tab.set_employee_available(False)

    def _on_daily_statuses(self, statuses: list) -> None:
        self._status_table.set_statuses(statuses)
        if self._view_model:
            code = self._view_model.selected_employee_code
            if code:
                self._status_table.select_employee(code)

    def _on_yearly_stats_requested(self, year: int) -> None:
        if not self._view_model:
            self.statusBar().showMessage("Inicializa el visor antes de generar estadísticas.")
            return
        self._view_model.request_yearly_statistics(year)

    def _on_yearly_stats_loading(self, year: int) -> None:
        self._stats_tab.set_loading(year)
        if hasattr(self, "_status_tabs"):
            self._status_tabs.setCurrentWidget(self._stats_tab)
        self.statusBar().showMessage(f"Generando estadísticas de {year}…")

    def _on_yearly_stats_ready(self, stats: YearlyStatistics) -> None:
        self._stats_tab.set_statistics(stats)
        self.statusBar().showMessage(f"Estadísticas de {stats.year} generadas.")

    def _on_yearly_stats_failed(self, message: str) -> None:
        self._stats_tab.set_error(message)
        self.statusBar().showMessage(message)

    def _on_yearly_stats_cleared(self) -> None:
        self._stats_tab.clear()

    def _on_employee_selected_from_model(self, code: str, name: str) -> None:
        self._current_employee_code = code
        self._status_table.select_employee(code)
        self._stats_tab.set_employee_available(True)
        self.statusBar().showMessage(f"Seleccionado: {name}")

    def _on_weekly_summary(self, cards: list[dict[str, object]]) -> None:
        self._summary_carousel.set_empty_message("Sin fichajes en la semana seleccionada.")
        self._summary_carousel.set_cards(cards)
        model = self._table.model()
        if model is not None:
            self._table.collapseAll()
            for row in range(model.rowCount()):
                parent_index = model.index(row, 0)
                status_index = model.index(row, 5)
                status = model.data(status_index, Qt.ItemDataRole.DisplayRole)
                if status in {"Trabajando", "Incompleto"}:
                    self._table.expand(parent_index)
        if not cards:
            self.statusBar().showMessage("Sin fichajes en la semana seleccionada.")
        else:
            self.statusBar().showMessage("Resumen semanal actualizado.")

    def _on_error(self, message: str) -> None:
        self.statusBar().showMessage(message)
        reply = QMessageBox.warning(
            self,
            "Error",
            message,
            QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Close,
        )
        if reply == QMessageBox.StandardButton.Retry:
            if self._view_model:
                if not self._view_model.has_employees():
                    self._view_model.reload_employees()
                else:
                    self._view_model.load()

    def _set_default_week(self) -> None:
        today = QDate.currentDate()
        start = today.addDays(-(today.dayOfWeek() - 1))
        end = start.addDays(6)
        self._filters.set_date_range(start, end)

    def resizeEvent(self, event) -> None:  # noqa: D401
        super().resizeEvent(event)
        self._update_overlay_geometry()

    def _update_overlay_geometry(self) -> None:
        if hasattr(self, "_busy_overlay") and self._busy_overlay:
            parent = self.centralWidget()
            if parent:
                self._busy_overlay.setGeometry(parent.rect())
                self._busy_overlay.raise_()
