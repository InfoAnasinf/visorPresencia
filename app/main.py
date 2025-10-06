"""Application entry point for the single-window experience."""

from __future__ import annotations

import sys
from typing import Optional

from PyQt6.QtWidgets import QApplication

from app.presentation.features.attendance.view import AttendanceWindow


def create_qapplication(argv: Optional[list[str]] = None) -> QApplication:
    """Create the QApplication instance with sensible defaults."""
    app = QApplication(argv or sys.argv)
    app.setOrganizationName("FinidiDev")
    app.setApplicationName("Visor de Presencia")
    return app


def main() -> int:
    """Start the GUI event loop."""
    app = create_qapplication()
    window = AttendanceWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

