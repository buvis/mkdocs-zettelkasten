import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from mkdocs_zettelkasten.plugin.utils.date_utils import convert_string_to_date

FIXED_TZ = ZoneInfo("Europe/London")


@patch("mkdocs_zettelkasten.plugin.utils.date_utils.tzlocal.get_localzone", return_value=FIXED_TZ)
def test_convert_string_to_date_standard_format(_mock_tz) -> None:
    result = convert_string_to_date("2024-04-23 12:34:56")
    expected = datetime.datetime(2024, 4, 23, 12, 34, 56, tzinfo=FIXED_TZ)

    assert result == expected


@patch("mkdocs_zettelkasten.plugin.utils.date_utils.tzlocal.get_localzone", return_value=FIXED_TZ)
def test_convert_string_to_date_compact_format(_mock_tz) -> None:
    result = convert_string_to_date("20240423123456")
    expected = datetime.datetime(2024, 4, 23, 12, 34, 56, tzinfo=FIXED_TZ)

    assert result == expected


@patch("mkdocs_zettelkasten.plugin.utils.date_utils.tzlocal.get_localzone", return_value=FIXED_TZ)
def test_convert_string_to_date_iso_format(_mock_tz) -> None:
    result = convert_string_to_date("2024-04-23T12:34:56")
    expected = datetime.datetime(2024, 4, 23, 12, 34, 56, tzinfo=FIXED_TZ)

    assert result == expected


def test_convert_string_to_date_invalid_string() -> None:
    result = convert_string_to_date("not a date")

    assert result is None


def test_convert_string_to_date_empty_string() -> None:
    result = convert_string_to_date("")

    assert result is None


def test_convert_string_to_date_none() -> None:
    result = convert_string_to_date(None)  # pyright: ignore[reportArgumentType]

    assert result is None


def test_convert_string_to_date_preserves_existing_timezone() -> None:
    result = convert_string_to_date(
        "2024-04-23T12:34:56+00:00", tz=ZoneInfo("US/Eastern")
    )
    assert result is not None
    assert result.tzinfo == datetime.timezone.utc


def test_convert_string_to_date_applies_tz_to_naive_iso() -> None:
    eastern = ZoneInfo("US/Eastern")
    result = convert_string_to_date("2024-04-23T12:34:56", tz=eastern)
    assert result is not None
    assert result.tzinfo is eastern


@patch("mkdocs_zettelkasten.plugin.utils.date_utils.tzlocal.get_localzone", return_value=FIXED_TZ)
def test_convert_string_to_date_already_datetime(_mock_tz) -> None:
    dt = datetime.datetime(2024, 4, 23, 12, 34, 56, tzinfo=FIXED_TZ)
    result = convert_string_to_date(dt)  # pyright: ignore[reportArgumentType]

    assert result == dt
