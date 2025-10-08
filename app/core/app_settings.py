"""High-level wrapper around QSettings for application preferences."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PyQt6.QtCore import QSettings


@dataclass(slots=True)
class SettingKey:
    """Strongly-typed keys used with QSettings."""

    group: str
    name: str

    def path(self) -> str:
        return f"{self.group}/{self.name}"


class AppSettings:
    """Centralised access to QSettings with optional secure storage."""

    def __init__(self) -> None:
        self._settings = QSettings(ORG_NAME, APP_NAME)

    def value(self, key: SettingKey, default: Any = None) -> Any:
        """Retrieve a value by key."""
        return self._settings.value(key.path(), default)

    def set_value(self, key: SettingKey, value: Any) -> None:
        """Persist a value."""
        self._settings.setValue(key.path(), value)

    def remove(self, key: SettingKey) -> None:
        """Remove a stored value."""
        self._settings.remove(key.path())


ORG_NAME = "FinidiDev"
APP_NAME = "VisorPresencia"

LAST_EMPLOYEE = SettingKey("ui", "last_employee_code")
THEME = SettingKey("ui", "theme")
