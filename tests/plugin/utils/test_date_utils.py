import datetime
import pytest
from mkdocs_zettelkasten.plugin.utils.date_utils import convert_string_to_date


def test_convert_string_to_date_standard_format():
    result = convert_string_to_date("2024-04-23 12:34:56")
    expected = datetime.datetime(2024, 4, 23, 12, 34, 56)
    assert result == expected


def test_convert_string_to_date_compact_format():
    result = convert_string_to_date("20240423123456")
    expected = datetime.datetime(2024, 4, 23, 12, 34, 56)
    assert result == expected


def test_convert_string_to_date_iso_format():
    result = convert_string_to_date("2024-04-23T12:34:56")
    expected = datetime.datetime(2024, 4, 23, 12, 34, 56)
    assert result == expected


def test_convert_string_to_date_invalid_string():
    result = convert_string_to_date("not a date")
    assert result == ""


def test_convert_string_to_date_empty_string():
    result = convert_string_to_date("")
    assert result == ""


def test_convert_string_to_date_none():
    result = convert_string_to_date(None)
    assert result == ""


def test_convert_string_to_date_already_datetime():
    dt = datetime.datetime(2024, 4, 23, 12, 34, 56)
    result = convert_string_to_date(dt)
    assert result == dt
