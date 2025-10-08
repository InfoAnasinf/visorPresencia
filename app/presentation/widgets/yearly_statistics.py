"""Widget displaying yearly statistics with charts and heatmaps."""

from __future__ import annotations

from datetime import date
from typing import Iterable

from PyQt6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QCategoryAxis,
    QChart,
    QChartView,
    QLineSeries,
    QValueAxis,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedLayout,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.domain.entities.yearly_statistics import DayLoad, YearlyStatistics

MONTH_LABELS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
WEEKDAY_LABELS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


class YearlyStatisticsTab(QWidget):
    """Presents yearly attendance analytics with charts and heatmaps."""

    generateRequested = pyqtSignal(int)

    _STATE_EMPTY = 0
    _STATE_LOADING = 1
    _STATE_READY = 2
    _STATE_ERROR = 3

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._is_loading = False
        self._employee_available = False
        self._last_year_requested: int | None = None
        self._build_ui()
        self.clear()

    def set_year_options(self, years: Iterable[int]) -> None:
        """Populate the combo box with available years."""
        unique_years = sorted({int(year) for year in years}, reverse=True)
        if not unique_years:
            unique_years = [date.today().year]
        current_year = date.today().year
        self._year_combo.blockSignals(True)
        self._year_combo.clear()
        for year in unique_years:
            self._year_combo.addItem(str(year), year)
        if current_year in unique_years:
            index = unique_years.index(current_year)
            self._year_combo.setCurrentIndex(index)
        else:
            self._year_combo.setCurrentIndex(0)
        self._year_combo.blockSignals(False)

    def set_employee_available(self, available: bool) -> None:
        """Enable or disable actions depending on employee selection."""
        self._employee_available = available
        if not available:
            self.clear(message="Selecciona un trabajador para generar estadísticas.")
        else:
            if self._stack.currentIndex() == self._STATE_EMPTY:
                self._message_label.setText("Pulsa «Generar informe» para obtener las estadísticas anuales.")
        self._update_controls_state()

    def clear(self, message: str | None = None) -> None:
        """Reset the view to the empty state."""
        self._is_loading = False
        if message:
            self._message_label.setText(message)
        else:
            prompt = (
                "Selecciona un trabajador y pulsa «Generar informe» para ver el resumen anual."
                if self._employee_available
                else "Selecciona un trabajador para generar estadísticas."
            )
            self._message_label.setText(prompt)
        self._set_state(self._STATE_EMPTY)
        self._update_controls_state()

    def set_loading(self, year: int) -> None:
        """Show loading state while the statistics are being generated."""
        self._is_loading = True
        self._last_year_requested = year
        self._loading_label.setText(f"Generando estadísticas de {year}…")
        self._set_state(self._STATE_LOADING)
        self._update_controls_state()

    def set_error(self, message: str) -> None:
        """Display an error message."""
        self._is_loading = False
        self._error_label.setText(message)
        self._set_state(self._STATE_ERROR)
        self._update_controls_state()

    def set_statistics(self, stats: YearlyStatistics) -> None:
        """Populate visualisations with the aggregated statistics."""
        self._is_loading = False
        self._update_summary(stats)
        self._update_monthly_chart(stats)
        self._update_weekday_chart(stats)
        self._update_cumulative_chart(stats)
        self._update_heatmap(stats)
        self._set_state(self._STATE_READY)
        self._update_controls_state()

    def selected_year(self) -> int:
        """Return the year currently selected in the combo box."""
        return int(self._year_combo.currentData(Qt.ItemDataRole.UserRole) or self._year_combo.currentText())

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        controls = QFrame(self)
        controls.setObjectName("YearlyStatsControls")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(12)

        year_label = QLabel("Año", controls)
        year_label.setObjectName("YearlyStatsYearLabel")
        controls_layout.addWidget(year_label)

        self._year_combo = QComboBox(controls)
        self._year_combo.setObjectName("YearlyStatsYearCombo")
        controls_layout.addWidget(self._year_combo)

        controls_layout.addStretch(1)

        self._generate_button = QPushButton("Generar informe", controls)
        self._generate_button.setObjectName("YearlyStatsGenerateButton")
        self._generate_button.clicked.connect(self._on_generate_clicked)
        controls_layout.addWidget(self._generate_button)

        layout.addWidget(controls)

        self._stack = QStackedLayout()
        layout.addLayout(self._stack, stretch=1)

        self._message_label = self._build_message_label()
        self._stack.addWidget(self._message_label)

        self._loading_label = self._build_message_label()
        self._loading_label.setObjectName("YearlyStatsLoadingLabel")
        self._stack.addWidget(self._loading_label)

        self._content_scroll = QScrollArea(self)
        self._content_scroll.setWidgetResizable(True)
        self._content_container = QWidget()
        self._content_scroll.setWidget(self._content_container)
        content_layout = QVBoxLayout(self._content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(18)

        self._summary_frame = QFrame(self._content_container)
        self._summary_frame.setObjectName("YearlyStatsSummaryFrame")
        summary_layout = QGridLayout(self._summary_frame)
        summary_layout.setContentsMargins(16, 16, 16, 16)
        summary_layout.setSpacing(12)
        self._summary_labels: dict[str, QLabel] = {}

        summary_definitions = [
            ("total_hours", "Horas totales"),
            ("worked_days", "Días trabajados"),
            ("average_hours", "Media por día"),
            ("top_day", "Día más largo"),
            ("low_day", "Día más ligero"),
        ]
        for index, (key, title) in enumerate(summary_definitions):
            card = self._create_summary_card(title)
            summary_layout.addWidget(card, index // 3, index % 3)
            self._summary_labels[key] = card.findChild(QLabel, "YearlySummaryValue")

        content_layout.addWidget(self._summary_frame)

        self._monthly_chart_view = self._create_chart_view()
        content_layout.addWidget(self._wrap_chart("Horas trabajadas por mes", self._monthly_chart_view))

        self._weekday_chart_view = self._create_chart_view()
        content_layout.addWidget(self._wrap_chart("Promedio de horas por día de la semana", self._weekday_chart_view))

        self._cumulative_chart_view = self._create_chart_view()
        content_layout.addWidget(self._wrap_chart("Acumulado anual de horas trabajadas", self._cumulative_chart_view))

        self._heatmap_table = self._create_heatmap_table()
        content_layout.addWidget(self._wrap_heatmap("Mapa de calor horario", self._heatmap_table))

        content_layout.addStretch(1)

        self._stack.addWidget(self._content_scroll)

        self._error_label = self._build_message_label()
        self._error_label.setObjectName("YearlyStatsErrorLabel")
        self._stack.addWidget(self._error_label)

        self.set_year_options(years=range(date.today().year - 3, date.today().year + 1))

    def _create_summary_card(self, title: str) -> QFrame:
        card = QFrame(self._summary_frame)
        card.setObjectName("YearlySummaryCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        title_label = QLabel(title, card)
        title_label.setObjectName("YearlySummaryTitle")
        layout.addWidget(title_label)

        value_label = QLabel("--", card)
        value_label.setObjectName("YearlySummaryValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(value_label)
        return card

    def _create_chart_view(self) -> QChartView:
        view = QChartView()
        view.setRenderHint(QPainter.RenderHint.Antialiasing)
        view.setMinimumHeight(260)
        view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return view

    def _create_heatmap_table(self) -> QTableWidget:
        table = QTableWidget(7, 24, self._content_container)
        table.setObjectName("YearlyStatsHeatmap")
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.horizontalHeader().setVisible(True)
        table.verticalHeader().setVisible(True)
        table.horizontalHeader().setDefaultSectionSize(44)
        table.verticalHeader().setDefaultSectionSize(32)
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setMinimumSectionSize(44)
        table.verticalHeader().setMinimumSectionSize(32)
        table.setHorizontalHeaderLabels([f"{hour:02d}" for hour in range(24)])
        table.setVerticalHeaderLabels(WEEKDAY_LABELS)
        for row in range(7):
            for column in range(24):
                item = QTableWidgetItem("")
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, column, item)
        table.setMinimumHeight(7 * 32 + table.horizontalHeader().height() + 24)
        return table

    def _wrap_chart(self, title: str, view: QChartView) -> QFrame:
        frame = QFrame(self._content_container)
        frame.setObjectName("YearlyStatsChartFrame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title_label = QLabel(title, frame)
        title_label.setObjectName("YearlyStatsChartTitle")
        layout.addWidget(title_label)
        layout.addWidget(view)
        return frame

    def _wrap_heatmap(self, title: str, table: QTableWidget) -> QFrame:
        frame = QFrame(self._content_container)
        frame.setObjectName("YearlyStatsHeatmapFrame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title_label = QLabel(title, frame)
        title_label.setObjectName("YearlyStatsChartTitle")
        layout.addWidget(title_label)
        layout.addWidget(table)

        legend = QLabel("Más oscuro: más minutos trabajados en esa franja horaria.", frame)
        legend.setObjectName("YearlyStatsHeatmapLegend")
        layout.addWidget(legend)

        return frame

    def _build_message_label(self) -> QLabel:
        label = QLabel("", self)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setMinimumHeight(160)
        label.setObjectName("YearlyStatsMessage")
        return label

    def _set_state(self, state: int) -> None:
        self._stack.setCurrentIndex(state)

    def _update_controls_state(self) -> None:
        self._year_combo.setEnabled(not self._is_loading)
        self._generate_button.setEnabled(self._employee_available and not self._is_loading)

    def _on_generate_clicked(self) -> None:
        if not self._employee_available or self._is_loading:
            return
        year = self.selected_year()
        self.generateRequested.emit(year)

    def _update_summary(self, stats: YearlyStatistics) -> None:
        self._summary_labels["total_hours"].setText(_format_minutes(stats.total_minutes))
        self._summary_labels["worked_days"].setText(str(stats.worked_days))
        average_minutes = stats.average_minutes_per_day
        average_text = f"{average_minutes / 60:.2f} h" if stats.worked_days else "--"
        self._summary_labels["average_hours"].setText(average_text)
        self._summary_labels["top_day"].setText(_format_day_load(stats.longest_day))
        self._summary_labels["low_day"].setText(_format_day_load(stats.shortest_day))

    def _update_monthly_chart(self, stats: YearlyStatistics) -> None:
        chart = QChart()
        chart.setTitle("Horas trabajadas por mes")
        series = QBarSeries(chart)
        bar_set = QBarSet("Horas")
        for minutes in stats.monthly_minutes:
            bar_set << minutes / 60.0
        bar_set.setColor(QColor("#2563eb"))
        series.append(bar_set)
        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(MONTH_LABELS)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%.0f")
        axis_y.setTitleText("Horas")
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().setVisible(False)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self._monthly_chart_view.setChart(chart)

    def _update_weekday_chart(self, stats: YearlyStatistics) -> None:
        chart = QChart()
        chart.setTitle("Promedio de horas por día de la semana")
        series = QLineSeries(chart)
        averages = []
        for index, total_minutes in enumerate(stats.weekday_minutes):
            occurrences = stats.weekday_occurrences[index] or 1
            average = (total_minutes / occurrences) / 60 if stats.weekday_occurrences[index] else 0
            series.append(float(index), average)
            averages.append(average)

        chart.addSeries(series)
        axis_x = QCategoryAxis()
        axis_x.setLabelsPosition(QCategoryAxis.AxisLabelsPosition.AxisLabelsPositionOnValue)
        for index, label in enumerate(WEEKDAY_LABELS):
            axis_x.append(label, float(index))
        axis_x.setRange(0.0, 6.0)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%.1f")
        axis_y.setTitleText("Horas")
        max_average = max(averages) if averages else 1
        axis_y.setRange(0, max(1.0, max_average * 1.2))
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().setVisible(False)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self._weekday_chart_view.setChart(chart)

    def _update_cumulative_chart(self, stats: YearlyStatistics) -> None:
        chart = QChart()
        chart.setTitle("Acumulado anual de horas trabajadas")
        series = QLineSeries(chart)
        cumulative = 0.0
        points = []
        for day_load in stats.daily_minutes:
            cumulative += day_load.minutes / 60.0
            day_of_year = day_load.day.timetuple().tm_yday
            series.append(float(day_of_year), cumulative)
            points.append((day_of_year, cumulative))

        chart.addSeries(series)

        axis_x = QValueAxis()
        axis_x.setLabelFormat("%d")
        axis_x.setTitleText("Día del año")
        axis_x.setRange(1, 366)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%.0f")
        axis_y.setTitleText("Horas acumuladas")
        max_value = points[-1][1] if points else 1.0
        axis_y.setRange(0, max(1.0, max_value * 1.1))
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().setVisible(False)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self._cumulative_chart_view.setChart(chart)

    def _update_heatmap(self, stats: YearlyStatistics) -> None:
        matrix = stats.heatmap
        max_minutes = max((value for row in matrix for value in row), default=0)
        for weekday, row in enumerate(matrix):
            for hour, minutes in enumerate(row):
                item = self._heatmap_table.item(weekday, hour)
                if item is None:
                    continue
                color = _color_for_minutes(minutes, max_minutes)
                item.setBackground(color)
                item.setText(_format_minutes(minutes) if minutes else "")
                tooltip = f"{WEEKDAY_LABELS[weekday]} {hour:02d}:00 — {minutes} min trabajados"
                item.setToolTip(tooltip)


def _format_minutes(total_minutes: int) -> str:
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


def _format_day_load(day_load: DayLoad | None) -> str:
    if not day_load:
        return "--"
    return f"{day_load.day.strftime('%d/%m')} · {_format_minutes(day_load.minutes)}"


def _color_for_minutes(minutes: int, max_minutes: int) -> QColor:
    if max_minutes <= 0 or minutes <= 0:
        return QColor("#eef2ff")
    intensity = min(1.0, minutes / max_minutes)
    base = QColor("#2563eb")
    alpha = int(60 + intensity * 175)
    color = QColor(base)
    color.setAlpha(alpha)
    return color
