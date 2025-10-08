"""Application entry point for the single-window experience."""

from __future__ import annotations

import sys
from typing import Optional

from PyQt6.QtWidgets import QApplication

from app.core.database import (
    build_settings_bundle,
    ensure_database_defaults,
    load_database_config,
)
from app.data.datasources.mssql import create_engine_from_config, create_session_factory
from app.data.repositories.attendance_repository import SqlAlchemyAttendanceRepository
from app.presentation.features.attendance.view import AttendanceWindow
from app.presentation.features.attendance.viewmodel import AttendanceViewModel


def create_qapplication(argv: Optional[list[str]] = None) -> QApplication:
    """Create the QApplication instance with sensible defaults."""
    app = QApplication(argv or sys.argv)
    app.setOrganizationName("FinidiDev")
    app.setApplicationName("Visor de Presencia")
    return app


def main() -> int:
    """Start the GUI event loop."""
    app = create_qapplication()
    window = _build_window()
    window.show()
    return app.exec()


def _build_window() -> AttendanceWindow:
    """Bootstrap dependencies and return the main window."""
    bundle = build_settings_bundle()
    ensure_database_defaults(bundle)
    db_config = load_database_config(bundle)

    engine = create_engine_from_config(db_config)
    session_factory = create_session_factory(engine)
    repository = SqlAlchemyAttendanceRepository(session_factory)
    view_model = AttendanceViewModel(repository, bundle.settings)

    window = AttendanceWindow()
    window.set_view_model(view_model)
    return window


if __name__ == "__main__":
    raise SystemExit(main())
