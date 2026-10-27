"""Тесты parser-ов: разбор одной записи CSV и JSONL."""

import pytest

from streamstats.errors import (
    InvalidEventError,
    InvalidTimestampError,
    UnsupportedFormatError,
)
from streamstats.parsers import detect_format, parse_csv_row, parse_jsonl_line
from tests.helpers import GOOD_LINE, make_json_line

PLACE = "file.jsonl, строка 2"


def test_parse_jsonl_line_returns_event() -> None:
    event = parse_jsonl_line(GOOD_LINE, PLACE)
    assert event["level"] == "INFO"
    assert event["source"] == "web"
    assert event["message"] == "ok"
    assert event["timestamp"].year == 2024


def test_parse_csv_row_returns_event() -> None:
    row = {
        "timestamp": "2024-01-01T10:00:00",
        "level": "ERROR",
        "source": "db",
        "message": "Ошибка",
    }
    event = parse_csv_row(row, "file.csv, строка 2")
    assert event["level"] == "ERROR"
    assert event["source"] == "db"


def test_parsers_keep_unicode() -> None:
    line = make_json_line("2024-01-01T10:00:00", "INFO", "сервер", "Привет, мир")
    event = parse_jsonl_line(line, PLACE)
    assert event["source"] == "сервер"
    assert event["message"] == "Привет, мир"

    row = {
        "timestamp": "2024-01-01T10:00:00",
        "level": "INFO",
        "source": "сервер",
        "message": "Привет, мир",
    }
    assert parse_csv_row(row, PLACE)["message"] == "Привет, мир"


def test_broken_json_reports_line() -> None:
    with pytest.raises(InvalidEventError, match="строка 2"):
        parse_jsonl_line("{это не json", PLACE)


def test_json_array_is_not_event() -> None:
    with pytest.raises(InvalidEventError):
        parse_jsonl_line("[1, 2, 3]", PLACE)


def test_csv_missing_value_is_error() -> None:
    row = {"timestamp": "2024-01-01T10:00:00", "level": "INFO", "source": None}
    with pytest.raises(InvalidEventError, match="source"):
        parse_csv_row(row, PLACE)


def test_bad_timestamp_reports_field_and_line() -> None:
    line = make_json_line("вчера", "INFO", "web", "ok")
    with pytest.raises(InvalidTimestampError) as info:
        parse_jsonl_line(line, PLACE)
    assert "timestamp" in str(info.value)
    assert "строка 2" in str(info.value)


def test_unknown_level_is_error() -> None:
    line = make_json_line("2024-01-01T10:00:00", "NOTICE", "web", "ok")
    with pytest.raises(InvalidEventError, match="NOTICE"):
        parse_jsonl_line(line, PLACE)


def test_empty_source_is_error() -> None:
    line = make_json_line("2024-01-01T10:00:00", "INFO", "  ", "ok")
    with pytest.raises(InvalidEventError, match="source"):
        parse_jsonl_line(line, PLACE)


def test_timestamp_with_z_is_ok() -> None:
    line = make_json_line("2024-01-01T10:00:00Z", "INFO", "web", "ok")
    event = parse_jsonl_line(line, PLACE)
    assert event["timestamp"].tzinfo is not None


def test_detect_format_by_extension() -> None:
    assert detect_format("data/log.CSV") == "csv"
    assert detect_format("log.jsonl") == "jsonl"
    with pytest.raises(UnsupportedFormatError):
        detect_format("log.txt")
