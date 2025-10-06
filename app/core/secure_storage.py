"""Secure credential management for database connectivity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from cryptography.fernet import Fernet
from PyQt6.QtCore import QByteArray

from app.core.app_settings import AppSettings, SettingKey


class KeyProvider(Protocol):
    """Protocol that hides how the encryption key is obtained."""

    def load_key(self) -> bytes:
        """Return the bytes for the symmetric key."""


@dataclass(slots=True)
class QSettingsKeyProvider:
    """Persist the encryption key in the OS-protected QSettings backend."""

    settings: AppSettings
    key_setting: SettingKey

    def load_key(self) -> bytes:
        stored = self.settings.value(self.key_setting)
        if isinstance(stored, QByteArray) and not stored.isEmpty():
            return stored.data()
        key = Fernet.generate_key()
        self.settings.set_value(self.key_setting, QByteArray(key))
        return key


class SecureCredentialsStorage:
    """Encrypts sensitive credentials before persisting them."""

    def __init__(self, settings: AppSettings, key_provider: KeyProvider) -> None:
        self._settings = settings
        self._fernet = Fernet(key_provider.load_key())

    def save_password(self, key: SettingKey, password: str) -> None:
        token = self._fernet.encrypt(password.encode("utf-8"))
        self._settings.set_value(key, QByteArray(token))

    def load_password(self, key: SettingKey) -> str | None:
        stored = self._settings.value(key)
        if not isinstance(stored, QByteArray) or stored.isEmpty():
            return None
        decrypted = self._fernet.decrypt(stored.data())
        return decrypted.decode("utf-8")

