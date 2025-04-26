import datetime
from zoneinfo import ZoneInfo

import tzlocal

from mkdocs_zettelkasten.plugin.utils.date_utils import convert_string_to_date

local_tz = ZoneInfo(tzlocal.get_localzone_name())


def test_convert_string_to_date_standard_format() -> None:
    result = convert_string_to_date("2024-04-23 12:34:56")
    expected = datetime.datetime(2024, 4, 23, 12, 34, 56, tzinfo=local_tz)

    assert result == expected


def test_convert_string_to_date_compact_format() -> None:
    result = convert_string_to_date("20240423123456")
    expected = datetime.datetime(2024, 4, 23, 12, 34, 56, tzinfo=local_tz)

    assert result == expected


def test_convert_string_to_date_iso_format() -> None:
    result = convert_string_to_date("2024-04-23T12:34:56")
    expected = datetime.datetime(2024, 4, 23, 12, 34, 56, tzinfo=local_tz)

    assert result == expected


def test_convert_string_to_date_invalid_string() -> None:
    result = convert_string_to_date("not a date")

    assert result is None


def test_convert_string_to_date_empty_string() -> None:
    result = convert_string_to_date("")

    assert result is None


def test_convert_string_to_date_none() -> None:
    result = convert_string_to_date(None)  # pyright: ignore[reportArgumentType]

    if result:
        pass

    assert result is None


def test_convert_string_to_date_already_datetime() -> None:
    dt = datetime.datetime(2024, 4, 23, 12, 34, 56, tzinfo=local_tz)
    result = convert_string_to_date(dt)  # pyright: ignore[reportArgumentType]

    assert result == dt
