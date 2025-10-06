"""SQL Server engine factory and session provider."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker


@dataclass(slots=True)
class SqlServerConfig:
    """Connection parameters for SQL Server."""

    host: str
    database: str
    username: str
    password: str
    port: Optional[int] = 1433
    driver: str = "ODBC Driver 17 for SQL Server"

    def to_uri(self) -> str:
        """Build a SQLAlchemy-compatible connection URI."""
        return (
            f"mssql+pyodbc://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
            f"?driver={self.driver.replace(' ', '+')}"
        )


def create_engine_from_config(config: SqlServerConfig) -> Engine:
    """Create a SQLAlchemy engine with sensible defaults."""
    engine = create_engine(
        config.to_uri(),
        pool_pre_ping=True,
        pool_recycle=1800,
        echo=False,
        future=True,
    )
    return engine


def create_session_factory(engine: Engine) -> sessionmaker:
    """Return a session factory bound to the provided engine."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

