"""DTO representing an employee for selection lists."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class EmployeeDTO:
    code: str
    display_name: str
    job_title: str | None = None
    photo: bytes | None = None
