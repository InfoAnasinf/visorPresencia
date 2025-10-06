"""Logging configuration for the application."""

from __future__ import annotations

import logging
from logging.config import dictConfig
from pathlib import Path


def configure_logging(log_dir: Path | None = None) -> None:
    """Configure structured logging with rotation-ready handlers."""
    log_dir = log_dir or Path.cwd() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    configuration = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "default",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "maxBytes": 1_000_000,
                "backupCount": 5,
                "formatter": "default",
                "filename": str(log_dir / "visor_presencia.log"),
                "encoding": "utf-8",
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "file"],
        },
    }
    dictConfig(configuration)

