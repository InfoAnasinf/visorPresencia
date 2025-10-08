"""View model coordinating employee selection and grouped weekly attendance."""

from __future__ import annotations

import logging
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import replace
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from time import perf_counter

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from app.core.app_settings import AppSettings, LAST_EMPLOYEE
from app.domain.entities.attendance_week import DailyAttendanceSummary, PunchInterval
from app.domain.entities.access_event import AccessEvent
from app.domain.entities.employee import Employee
from app.domain.entities.weekly_metrics import WeeklyMetrics
from app.domain.usecases.load_employees import load_employees
from app.domain.usecases.load_daily_statuses import load_daily_statuses
from app.domain.usecases.load_weekly_attendance import load_weekly_attendance
from app.domain.usecases.load_recent_accesses import load_recent_accesses
from app.domain.usecases.load_yearly_statistics import load_yearly_statistics
from app.presentation.features.attendance.model import AttendanceTreeModel, DayRow, IntervalRow
from app.presentation.utils.i18n import spanish_weekday_abbrev


class FiltersState:
    __slots__ = ("date_from", "date_to")

    def __init__(self) -> None:
        self.date_from: date | None = None
        self.date_to: date | None = None


ACCESS_POLL_INTERVAL_MS = 3000  # 3 seconds for near-real-time refresh
ACCESS_BASELINE_LIMIT = 500
ACCESS_FETCH_LIMIT = 200
ACCESS_EVENT_CACHE_SIZE = 512
SIMULATION_INTERVAL_MS = 10_000
ACCESS_POLL_WINDOW = timedelta(hours=2)  # TODO: revert to minutes=1 for producción


class AttendanceViewModel(QObject):
    """Binds domain data with the Qt models."""

    errorOccurred = pyqtSignal(str)
    loadingChanged = pyqtSignal(bool)
    employeesLoaded = pyqtSignal(list)
    employeeSelectionChanged = pyqtSignal(str, str)
    weeklySummaryReady = pyqtSignal(object)
    employeeCardReady = pyqtSignal(object)
    weeklyMetricsReady = pyqtSignal(object)
    dailyStatusesReady = pyqtSignal(list)
    accessEventRaised = pyqtSignal(object)
    yearlyStatisticsLoading = pyqtSignal(int)
    yearlyStatisticsReady = pyqtSignal(object)
    yearlyStatisticsFailed = pyqtSignal(str)
    yearlyStatisticsCleared = pyqtSignal()

    def __init__(self, repository, settings: AppSettings, enable_monitoring: bool = True) -> None:
        super().__init__()
        self._repository = repository
        self._settings = settings
        self._model = AttendanceTreeModel()
        self._filters = FiltersState()
        self._employees: List[Employee] = []
        self._selected: Optional[Employee] = None
        self._week_start: date | None = None
        self._week_end: date | None = None
        self._days: List[DayRow] = []
        self._metrics: WeeklyMetrics | None = None
        self._monitor_enabled = enable_monitoring
        self._logger = logging.getLogger("attendance.access_monitor")
        self._configure_logger()
        self._stats_logger = logging.getLogger("attendance.statistics")
        self._configure_statistics_logger()
        self._access_timer: QTimer | None = None
        self._access_executor: ThreadPoolExecutor | None = None
        self._access_future: Future | None = None
        self._warmup_future: Future | None = None
        self._monitor_ready = False
        self._last_access_timestamp: datetime = datetime.now()
        self._seen_event_buffer: deque[tuple[str, datetime]] = deque()
        self._seen_event_lookup: set[str] = set()
        self._daily_event_counts: dict[tuple[str, date], int] = {}
        self._simulation_timer: QTimer | None = None
        self._simulation_employees: list[tuple[str, str]] = [
            ("SIM001", "Demostracion"),
        ]
        self._last_poll_timestamp: datetime | None = None
        self._poll_window = ACCESS_POLL_WINDOW
        self._stats_executor: ThreadPoolExecutor | None = ThreadPoolExecutor(max_workers=1)
        self._stats_future: Future | None = None
        self._stats_generation_counter = 0
        self._stats_requests: Dict[int, Tuple[float, str, int]] = {}
        self.destroyed.connect(self._shutdown_statistics_executor)
        if self._monitor_enabled:
            self._access_timer = QTimer(self)
            self._access_timer.setInterval(ACCESS_POLL_INTERVAL_MS)
            self._access_timer.timeout.connect(self._on_access_timer)
            self._access_timer.start(ACCESS_POLL_INTERVAL_MS)
            self._logger.debug("Temporizador de sondeo iniciado (intervalo=%sms)", ACCESS_POLL_INTERVAL_MS)
            self._access_executor = ThreadPoolExecutor(max_workers=1)
            self.destroyed.connect(self._shutdown_access_monitor)
            self._schedule_access_warmup()

    def _configure_logger(self) -> None:
        if self._logger.handlers:
            return
        self._logger.setLevel(logging.DEBUG)
        self._logger.propagate = False
        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_dir / "access_monitor.log", encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    def _configure_statistics_logger(self) -> None:
        if self._stats_logger.handlers:
            return
        self._stats_logger.setLevel(logging.DEBUG)
        self._stats_logger.propagate = False
        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_dir / "yearly_statistics.log", encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        self._stats_logger.addHandler(handler)

    def initialize(self) -> None:
        self._load_employees()

    def reload_employees(self) -> None:
        self._load_employees()

    @property
    def model(self) -> AttendanceTreeModel:
        return self._model

    def has_employees(self) -> bool:
        return bool(self._employees)

    def has_selected_employee(self) -> bool:
        return self._selected is not None

    @property
    def selected_employee_code(self) -> str | None:
        return self._selected.code if self._selected else None

    def load(self) -> None:
        if not self._selected:
            if self._employees:
                self.errorOccurred.emit("Selecciona un trabajador para cargar los fichajes.")
            return
        if not self._week_start or not self._week_end:
            self.errorOccurred.emit("Selecciona un rango semanal valido.")
            return

        reference = datetime.now()
        self.loadingChanged.emit(True)
        try:
            summaries = load_weekly_attendance(
                self._repository,
                self._selected.code,
                self._week_start,
                reference=reference,
            )
            self._days = self._build_day_rows(summaries, reference.date())
            filtered = self._apply_filters(self._days)
            self._model.set_days(filtered)
            self.weeklySummaryReady.emit(self._build_summary_cards(self._days))
            self._metrics = self._build_metrics(self._days)
            if self._metrics:
                self.weeklyMetricsReady.emit(self._metrics)
            self._load_daily_statuses(reference.date())
        except Exception as exc:  # noqa: BLE001
            self.errorOccurred.emit(str(exc))
        finally:
            self.loadingChanged.emit(False)

    def update_date_range(self, date_from, date_to) -> None:
        self._filters.date_from = date_from.toPyDate() if date_from else None
        self._filters.date_to = date_to.toPyDate() if date_to else None
        self._week_start = self._filters.date_from
        self._week_end = self._filters.date_to

    def clear_filters(self) -> None:
        self._filters = FiltersState()
        self._filters.date_from = self._week_start
        self._filters.date_to = self._week_end
        self._model.set_days(self._apply_filters(self._days))

    # --- simulation helpers -------------------------------------------------
    def start_fake_access_simulation(self, interval_ms: int = SIMULATION_INTERVAL_MS) -> None:
        if self._simulation_timer is None:
            self._simulation_timer = QTimer(self)
            self._simulation_timer.timeout.connect(self._emit_simulated_access_event)
        if interval_ms <= 0:
            interval_ms = SIMULATION_INTERVAL_MS
        self._simulation_timer.setInterval(interval_ms)
        if not self._simulation_timer.isActive():
            self._reset_simulation_state()
            self._simulation_timer.start()
            self._logger.info("Simulacion demo iniciada (intervalo=%sms)", interval_ms)
            self._emit_simulated_access_event()

    def _reset_simulation_state(self) -> None:
        today = date.today()
        self._daily_event_counts = {(code, today): 0 for code, _ in self._simulation_employees}
        self._last_access_timestamp = datetime.now()
        self._logger.debug("Estado de simulacion reiniciado para %d empleados", len(self._simulation_employees))

    def _emit_simulated_access_event(self) -> None:
        if not self._simulation_employees:
            return
        code, name = self._simulation_employees[0]
        timestamp = datetime.now()
        self._logger.debug("Evento simulado generado: %s %s", code, timestamp.isoformat())
        event = AccessEvent(
            timestamp=timestamp,
            employee_code=code,
            employee_name=f"{name} (demo)",
            badge="SIM-DEMO",
        )
        payload = self._register_new_access_event(event)
        if payload:
            self.accessEventRaised.emit(payload)

    def stop_fake_access_simulation(self) -> None:
        if self._simulation_timer and self._simulation_timer.isActive():
            self._simulation_timer.stop()
            self._logger.info("Simulacion demo detenida")

    def is_fake_simulation_active(self) -> bool:
        return bool(self._simulation_timer and self._simulation_timer.isActive())

    def select_employee(self, code: str) -> None:
        employee = next((emp for emp in self._employees if emp.code == code), None)
        if not employee:
            return
        self._selected = employee
        self._settings.set_value(LAST_EMPLOYEE, employee.code)
        self.employeeSelectionChanged.emit(employee.code, employee.display_name)
        self.employeeCardReady.emit(employee)
        self._reset_yearly_statistics_state()
        self.load()

    def request_yearly_statistics(self, year: int) -> None:
        if not self._selected:
            self.errorOccurred.emit("Selecciona un trabajador para generar estadísticas.")
            return
        executor = self._stats_executor
        if executor is None:
            executor = ThreadPoolExecutor(max_workers=1)
            self._stats_executor = executor
        self._stats_generation_counter += 1  # incr
        request_id = self._stats_generation_counter
        employee_code = self._selected.code
        started_at = perf_counter()
        self._stats_requests[request_id] = (started_at, employee_code, year)
        self._stats_logger.info(
            "Inicio estadísticas anuales: req=%d empleado=%s año=%d",
            request_id,
            employee_code,
            year,
        )
        self.yearlyStatisticsLoading.emit(year)
        future = executor.submit(
            load_yearly_statistics,
            self._repository,
            employee_code,
            year,
        )
        self._stats_future = future
        future.add_done_callback(
            lambda fut, rid=request_id, code=employee_code, target_year=year: self._handle_yearly_statistics_future(
                rid,
                code,
                target_year,
                fut,
            )
        )
        self._stats_logger.debug("Callback registrado para req=%d futuro=%s", request_id, future)

    def _load_employees(self) -> None:
        self._reset_yearly_statistics_state()
        self.loadingChanged.emit(True)
        try:
            employees = load_employees(self._repository)
            self._employees = employees
            self.employeesLoaded.emit(employees)
            last_code = self._settings.value(LAST_EMPLOYEE)
            if last_code:
                self.select_employee(str(last_code))
            else:
                self._load_daily_statuses(date.today())
        except Exception as exc:  # noqa: BLE001
            self.errorOccurred.emit(f"Error al cargar trabajadores: {exc}")
        finally:
            self.loadingChanged.emit(False)

    def _build_day_rows(
        self,
        summaries: List[DailyAttendanceSummary],
        today: date,
    ) -> List[DayRow]:
        days: List[DayRow] = []
        for summary in summaries:
            intervals = [self._interval_to_row(interval) for interval in summary.intervals]
            status = self._day_status(summary, today)
            day_row = DayRow(
                day=summary.day,
                total_minutes=summary.total_minutes,
                status=status,
                is_incomplete=summary.has_incomplete,
                is_current=summary.day == today,
                intervals=intervals,
            )
            days.append(day_row)
        days.sort(key=lambda item: item.day)
        return days

    def _interval_to_row(self, interval: PunchInterval) -> IntervalRow:
        if interval.is_incomplete:
            status = "Incompleto"
        elif interval.is_active:
            status = "Trabajando"
        else:
            status = "Completado"
        return IntervalRow(
            incidence=interval.incidence,
            start=interval.start,
            end=interval.end,
            duration_minutes=interval.minutes,
            status=status,
            is_active=interval.is_active,
            is_incomplete=interval.is_incomplete,
        )

    def _day_status(self, summary: DailyAttendanceSummary, today: date) -> str:
        if summary.has_incomplete:
            return "Incompleto"
        if summary.day == today and summary.is_working:
            return "Trabajando"
        return "Completado"

    def _apply_filters(self, days: List[DayRow]) -> List[DayRow]:
        if not days:
            return []

        result: List[DayRow] = []
        for day in days:
            if self._filters.date_from and day.day < self._filters.date_from:
                continue
            if self._filters.date_to and day.day > self._filters.date_to:
                continue
            result.append(day)
        return result


    def _build_summary_cards(self, days: List[DayRow]) -> list[dict[str, object]]:
        cards: list[dict[str, object]] = []
        for day in days:
            hours, minutes = divmod(day.total_minutes, 60)
            cards.append(
                {
                    "weekday": spanish_weekday_abbrev(day.day, capitalize=True),
                    "date_label": day.day.strftime("%d/%m"),
                    "hours_label": f"{hours:02}:{minutes:02}",
                    "status": day.status,
                    "is_current": day.is_current,
                    "is_incomplete": day.is_incomplete,
                }
            )
        return cards

    def _build_metrics(self, days: List[DayRow]) -> WeeklyMetrics | None:
        total_minutes = sum(day.total_minutes for day in days) if days else 0
        incomplete = sum(1 for day in days if day.is_incomplete) if days else 0
        worked = sum(1 for day in days if day.total_minutes > 0) if days else 0
        return WeeklyMetrics(total_minutes=total_minutes, incomplete_days=incomplete, worked_days=worked)

    def _load_daily_statuses(self, reference: date) -> None:
        try:
            statuses = load_daily_statuses(self._repository, reference)
            self.dailyStatusesReady.emit(statuses)
        except Exception as exc:  # noqa: BLE001
            self.errorOccurred.emit(f"Error al obtener estados diarios: {exc}")

    # --- access monitoring -------------------------------------------------
    def _schedule_access_warmup(self) -> None:
        if not self._monitor_enabled or self._access_executor is None:
            return
        if self._warmup_future is not None:
            return
        baseline_since = datetime.now() - self._poll_window
        self._logger.debug("Iniciando warmup de fichajes desde %s", baseline_since.isoformat())
        self._warmup_future = self._access_executor.submit(
            load_recent_accesses,
            self._repository,
            baseline_since,
            ACCESS_BASELINE_LIMIT,
        )
        self._warmup_future.add_done_callback(self._handle_warmup_future)

    def _handle_warmup_future(self, future: Future) -> None:
        try:
            events = future.result()
        except Exception as exc:  # noqa: BLE001
            self._logger.exception("Fallo en warmup de monitor de fichajes")
            QTimer.singleShot(
                0,
                lambda exc=exc: self.errorOccurred.emit(
                    f"No se pudo inicializar el monitor de fichajes: {exc}"
                ),
            )
            events = []
        try:
            self._complete_access_warmup(events)
        except Exception as exc:  # noqa: BLE001
            self._logger.exception("Error al completar warmup: %s", exc)

    def _complete_access_warmup(self, events: List[AccessEvent]) -> None:
        self._warmup_future = None
        latest = self._last_access_timestamp
        self._logger.debug("Warmup completado con %d eventos", len(events))
        for event in events:
            self._register_baseline_event(event)
            latest = max(latest, event.timestamp)
        self._last_access_timestamp = latest if events else datetime.now()
        self._monitor_ready = True
        if self._access_timer and not self._access_timer.isActive():
            self._access_timer.start(ACCESS_POLL_INTERVAL_MS)
            self._logger.debug("Temporizador de sondeo reactivado tras warmup")

    def _on_access_timer(self) -> None:
        if not self._monitor_enabled:
            return
        if not self._monitor_ready:
            self._logger.debug("Sondeo omitido: monitor aun no listo")
            return
        if self._access_executor is None:
            return
        if self._access_future and not self._access_future.done():
            self._logger.debug("Consulta previa aun en ejecucion; se omite el ciclo de sondeo")
            return
        since = datetime.now() - self._poll_window
        self._prune_seen_events(since)
        now = datetime.now()
        interval = (now - self._last_poll_timestamp).total_seconds() if self._last_poll_timestamp else 0.0
        self._logger.debug("Programando consulta de fichajes desde %s (intervalo %.2fs)", since.isoformat(), interval)
        self._logger.debug("Ventana de consulta: %ss", self._poll_window.total_seconds())
        self._last_poll_timestamp = now
        self._access_future = self._access_executor.submit(
            load_recent_accesses,
            self._repository,
            since,
            ACCESS_FETCH_LIMIT,
        )
        self._access_future.add_done_callback(self._handle_access_future)

    def _handle_access_future(self, future: Future) -> None:
        try:
            events = future.result()
        except Exception as exc:  # noqa: BLE001
            self._logger.exception("Error al consultar fichajes recientes")
            QTimer.singleShot(
                0,
                lambda exc=exc: self.errorOccurred.emit(
                    f"Error al vigilar fichajes: {exc}"
                ),
            )
            return
        if not events:
            self._logger.debug("Sin fichajes nuevos desde la ultima consulta")
            return
        self._logger.debug("Consulta devolvio %d registros nuevos", len(events))
        self._process_access_events(events)

    def _process_access_events(self, events: List[AccessEvent]) -> None:
        latest = self._last_access_timestamp
        self._logger.debug("Procesando %d eventos recibidos", len(events))
        for event in events:
            latest = max(latest, event.timestamp)
            payload = self._register_new_access_event(event)
            if payload:
                self.accessEventRaised.emit(payload)
        self._last_access_timestamp = latest

    def _register_baseline_event(self, event: AccessEvent) -> None:
        key = self._event_key(event)
        self._mark_event_seen(key, event.timestamp)
        self._increment_daily_count(event)
        self._logger.debug("Registrando evento en warmup: %s %s", event.employee_code, event.timestamp.isoformat())

    def _register_new_access_event(self, event: AccessEvent) -> dict[str, object] | None:
        key = self._event_key(event)
        if key in self._seen_event_lookup:
            self._logger.debug("Evento duplicado ignorado: %s", key)
            return None
        self._mark_event_seen(key, event.timestamp)
        sequence = self._increment_daily_count(event)
        is_entry = sequence % 2 == 1
        origin = "simulacion" if event.badge == "SIM-DEMO" else "bd"
        self._logger.info("Nuevo fichaje detectado (%s): code=%s time=%s entry=%s seq=%d", origin, event.employee_code, event.timestamp.isoformat(), is_entry, sequence)
        return {
            "timestamp": event.timestamp,
            "employee_code": event.employee_code,
            "employee_name": event.employee_name,
            "badge": event.badge,
            "sequence": sequence,
            "is_entry": is_entry,
        }

    def _event_key(self, event: AccessEvent) -> str:
        badge = event.badge or ""
        return f"{event.employee_code}:{event.timestamp.isoformat()}:{badge}"

    def _mark_event_seen(self, key: str, timestamp: datetime) -> None:
        self._seen_event_buffer.append((key, timestamp))
        self._seen_event_lookup.add(key)
        if len(self._seen_event_buffer) > ACCESS_EVENT_CACHE_SIZE:
            removed_key, _ = self._seen_event_buffer.popleft()
            self._seen_event_lookup.discard(removed_key)

    def _increment_daily_count(self, event: AccessEvent) -> int:
        day_key = (event.employee_code, event.timestamp.date())
        count = self._daily_event_counts.get(day_key, 0) + 1
        self._daily_event_counts[day_key] = count
        self._prune_daily_counts(event.timestamp.date())
        return count

    def _prune_daily_counts(self, reference: date) -> None:
        cutoff = reference - timedelta(days=3)
        obsolete = [
            key for key in self._daily_event_counts if key[1] < cutoff
        ]
        for key in obsolete:
            self._daily_event_counts.pop(key, None)

    def _prune_seen_events(self, threshold: datetime) -> None:
        changed = False
        while self._seen_event_buffer and self._seen_event_buffer[0][1] < threshold:
            removed_key, _ = self._seen_event_buffer.popleft()
            if removed_key in self._seen_event_lookup:
                self._seen_event_lookup.discard(removed_key)
                changed = True
        if changed:
            self._logger.debug("Purgada cache de fichajes vistos. Total actual: %d", len(self._seen_event_lookup))

    def reset_seen_events(self) -> None:
        """Clear cached punches so they can be reported again."""
        self._seen_event_buffer.clear()
        self._seen_event_lookup.clear()
        self._daily_event_counts.clear()
        self._logger.info("Cache de fichajes vistos reiniciada manualmente")

    def _shutdown_access_monitor(self) -> None:
        self._logger.debug("Apagando monitor de accesos")
        if self._access_timer:
            self._access_timer.stop()
        if self._access_executor:
            self._access_executor.shutdown(wait=False, cancel_futures=True)
        if self._simulation_timer:
            self._simulation_timer.stop()

    def _handle_yearly_statistics_future(
        self,
        request_id: int,
        employee_code: str,
        year: int,
        future: Future,
    ) -> None:
        self._stats_logger.debug(
            "Callback completado para req=%d futuro=%s (done=%s, cancelled=%s)",
            request_id,
            future,
            future.done(),
            future.cancelled(),
        )
        def notify() -> None:
            self._stats_logger.debug("Procesando notify para req=%d", request_id)
            if request_id != self._stats_generation_counter:
                self._stats_logger.debug(
                    "Descartando estadísticas req=%d por id fuera de fecha (actual=%d)",
                    request_id,
                    self._stats_generation_counter,
                )
                self._stats_requests.pop(request_id, None)
                return
            if not self._selected or self._selected.code != employee_code:
                self._stats_logger.debug(
                    "Descartando estadísticas req=%d por cambio de empleado (seleccionado=%s)",
                    request_id,
                    self._selected.code if self._selected else None,
                )
                self._stats_requests.pop(request_id, None)
                return
            if self._stats_future is future:
                self._stats_future = None
            meta = self._stats_requests.pop(request_id, None)
            try:
                stats = future.result()
            except Exception as exc:  # noqa: BLE001
                self._stats_logger.error(
                    "Error estadísticas anuales: req=%d empleado=%s año=%d error=%s",
                    request_id,
                    employee_code,
                    year,
                    exc,
                )
                self.yearlyStatisticsFailed.emit(f"Error al generar estadísticas {year}: {exc}")
            else:
                elapsed = (perf_counter() - meta[0]) if meta else 0.0
                self._stats_logger.info(
                    "Estadísticas listas: req=%d empleado=%s año=%d minutos=%d dias=%d tiempo=%.2fs",
                    request_id,
                    employee_code,
                    year,
                    getattr(stats, "total_minutes", 0),
                    getattr(stats, "worked_days", 0),
                    elapsed,
                )
                self._stats_logger.debug("Emitiendo señal yearlyStatisticsReady para req=%d", request_id)
                self.yearlyStatisticsReady.emit(stats)

        notify()

    def _reset_yearly_statistics_state(self) -> None:
        self._stats_generation_counter += 1  # incr
        if self._stats_future and not self._stats_future.done():
            self._stats_future.cancel()
        self._stats_future = None
        self._stats_requests.clear()
        self.yearlyStatisticsCleared.emit()

    def _shutdown_statistics_executor(self) -> None:
        if self._stats_executor:
            self._stats_executor.shutdown(wait=False, cancel_futures=True)
            self._stats_executor = None
        self._stats_future = None
        self._stats_requests.clear()















