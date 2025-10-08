"""Domain entity representing a selectable employee."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Employee:
    code: str
    display_name: str
    job_title: str | None = None
    photo: bytes | None = None
