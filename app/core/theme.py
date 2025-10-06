"""Theme loader and palette definitions."""

from __future__ import annotations

from importlib import resources
from typing import Literal


ThemeName = Literal["light", "dark"]


def load_theme(theme: ThemeName) -> str:
    """Return the QSS contents for the chosen theme."""
    name = "light.qss" if theme == "light" else "dark.qss"
    with resources.files("assets.qss").joinpath(name).open("r", encoding="utf-8") as fh:
        return fh.read()

