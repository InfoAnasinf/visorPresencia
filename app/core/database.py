"""Database configuration helpers backed by QSettings with encryption."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.app_settings import AppSettings, SettingKey
from app.core.secure_storage import QSettingsKeyProvider, SecureCredentialsStorage
from app.data.datasources.mssql import SqlServerConfig


DB_HOST = SettingKey("database", "host")
DB_NAME = SettingKey("database", "name")
DB_USER = SettingKey("database", "user")
DB_DRIVER = SettingKey("database", "driver")
DB_PASSWORD = SettingKey("database_secure", "password")
ENCRYPTION_KEY = SettingKey("secrets", "fernet_key")


@dataclass(slots=True)
class DatabaseSettingsBundle:
    """Container holding resolved configuration helpers."""

    settings: AppSettings
    secure_storage: SecureCredentialsStorage


DEFAULT_CREDENTIALS = SqlServerConfig(
    host="188.213.7.76",
    database="Fichajes",
    username="sa",
    password="V!c4W-85bX",
    driver="ODBC Driver 17 for SQL Server",
)


def build_settings_bundle() -> DatabaseSettingsBundle:
    """Create settings + secure storage ready for use."""
    settings = AppSettings()
    key_provider = QSettingsKeyProvider(settings=settings, key_setting=ENCRYPTION_KEY)
    secure_storage = SecureCredentialsStorage(settings=settings, key_provider=key_provider)
    return DatabaseSettingsBundle(settings=settings, secure_storage=secure_storage)


def ensure_database_defaults(bundle: DatabaseSettingsBundle) -> None:
    """Persist default credentials if none have been stored yet."""
    settings = bundle.settings
    secure_storage = bundle.secure_storage

    if settings.value(DB_HOST) is None:
        settings.set_value(DB_HOST, DEFAULT_CREDENTIALS.host)
    if settings.value(DB_NAME) is None:
        settings.set_value(DB_NAME, DEFAULT_CREDENTIALS.database)
    if settings.value(DB_USER) is None:
        settings.set_value(DB_USER, DEFAULT_CREDENTIALS.username)
    if settings.value(DB_DRIVER) is None:
        settings.set_value(DB_DRIVER, DEFAULT_CREDENTIALS.driver)
    if secure_storage.load_password(DB_PASSWORD) is None:
        secure_storage.save_password(DB_PASSWORD, DEFAULT_CREDENTIALS.password)


def load_database_config(bundle: DatabaseSettingsBundle) -> SqlServerConfig:
    """Return the SQL Server configuration from persisted settings."""
    settings = bundle.settings
    secure_storage = bundle.secure_storage

    host = _require_setting(settings, DB_HOST)
    database = _require_setting(settings, DB_NAME)
    username = _require_setting(settings, DB_USER)
    driver = settings.value(DB_DRIVER, DEFAULT_CREDENTIALS.driver)
    password = secure_storage.load_password(DB_PASSWORD)

    if password is None:
        raise ValueError("No hay contrasena almacenada para la base de datos.")

    return SqlServerConfig(
        host=host,
        database=database,
        username=username,
        password=password,
        driver=driver,
    )


def _require_setting(settings: AppSettings, key: SettingKey) -> str:
    value = settings.value(key)
    if not value:
        raise ValueError(f"Falta la clave de configuracion: {key.path()}")
    return str(value)

