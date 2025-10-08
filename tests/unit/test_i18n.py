from datetime import date

from app.presentation.utils.i18n import spanish_weekday_abbrev, spanish_weekday_name


def test_spanish_weekday_name_returns_lowercase():
    assert spanish_weekday_name(date(2025, 1, 1)) == "miércoles"


def test_spanish_weekday_abbrev_capitalize():
    assert spanish_weekday_abbrev(date(2025, 1, 1), capitalize=True) == "Mié"
