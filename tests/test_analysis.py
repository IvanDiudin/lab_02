"""Тесты чтения файлов, подсчёта статистики и отчёта."""

from pathlib import Path

import pytest

from streamstats.analysis import analyze_files, get_top_items
from streamstats.errors import InvalidEventError, UnsupportedFormatError
from streamstats.report import build_report
from tests.helpers import CSV_TEXT, GOOD_LINE, JSONL_TEXT, write_file


def test_empty_csv_gives_zero_report(tmp_path: Path) -> None:
    path = write_file(tmp_path, "empty.csv", "")
    report = build_report(analyze_files([path], "csv", False))
    assert report["total_events"] == 0
    assert report["first_timestamp"] is None
    assert report["last_timestamp"] is None
    assert report["events_by_level"]["ERROR"] == 0
    assert report["top_error_sources"] == []


def test_empty_jsonl_gives_zero_report(tmp_path: Path) -> None:
    path = write_file(tmp_path, "empty.jsonl", "")
    report = build_report(analyze_files([path], "jsonl", False))
    assert report["total_events"] == 0


def test_csv_and_jsonl_give_same_report(tmp_path: Path) -> None:
    csv_path = write_file(tmp_path, "log.csv", CSV_TEXT)
    jsonl_path = write_file(tmp_path, "log.jsonl", JSONL_TEXT)
    csv_report = build_report(analyze_files([csv_path], "csv", False))
    jsonl_report = build_report(analyze_files([jsonl_path], "jsonl", False))
    assert csv_report == jsonl_report


def test_report_values(tmp_path: Path) -> None:
    path = write_file(tmp_path, "log.csv", CSV_TEXT)
    report = build_report(analyze_files([path], "csv", False))
    assert report["total_events"] == 4
    assert report["events_by_level"]["ERROR"] == 2
    assert report["events_by_source"] == {"db": 2, "web": 2}
    assert report["top_error_sources"][0] == {"source": "db", "count": 2}
    assert report["first_timestamp"].startswith("2024-01-01T10:00:00")
    assert report["last_timestamp"].startswith("2024-01-01T10:15:00")


def test_several_files_are_merged_without_loss(tmp_path: Path) -> None:
    first = write_file(tmp_path, "a.csv", CSV_TEXT)
    second = write_file(tmp_path, "b.jsonl", JSONL_TEXT)
    stats = analyze_files([first, second], None, False)
    assert stats["total"] == 8
    assert stats["levels"]["ERROR"] == 4


def test_unicode_is_kept_in_report(tmp_path: Path) -> None:
    path = write_file(tmp_path, "ru.csv", CSV_TEXT.replace("web", "сервер"))
    report = build_report(analyze_files([path], "csv", False))
    assert "сервер" in report["events_by_source"]


def test_blank_lines_in_jsonl_are_ignored(tmp_path: Path) -> None:
    text = GOOD_LINE + "\n\n" + GOOD_LINE + "\n"
    path = write_file(tmp_path, "blank.jsonl", text)
    stats = analyze_files([path], "jsonl", False)
    assert stats["total"] == 2
    assert stats["skipped"] == 0


def test_bad_json_in_line_7_reports_line_7(tmp_path: Path) -> None:
    lines = [GOOD_LINE] * 6 + ["{это не json"] + [GOOD_LINE]
    path = write_file(tmp_path, "bad.jsonl", "\n".join(lines) + "\n")
    with pytest.raises(InvalidEventError, match="строка 7"):
        analyze_files([path], "jsonl", False)


def test_csv_missing_value_reports_line(tmp_path: Path) -> None:
    text = "timestamp,level,source,message\n2024-01-01T10:00:00,INFO\n"
    path = write_file(tmp_path, "bad.csv", text)
    with pytest.raises(InvalidEventError, match="строка 2"):
        analyze_files([path], "csv", False)


def test_skip_invalid_counts_other_lines(tmp_path: Path) -> None:
    text = GOOD_LINE + "\n{плохо\n" + GOOD_LINE + "\n"
    path = write_file(tmp_path, "mixed.jsonl", text)
    stats = analyze_files([path], "jsonl", True)
    assert stats["total"] == 2
    assert stats["skipped"] == 1


def test_without_skip_invalid_processing_stops(tmp_path: Path) -> None:
    text = GOOD_LINE + "\n{плохо\n" + GOOD_LINE + "\n"
    path = write_file(tmp_path, "mixed.jsonl", text)
    with pytest.raises(InvalidEventError):
        analyze_files([path], "jsonl", False)


def test_top_is_sorted_deterministically() -> None:
    counts = {"b": 1, "a": 1, "c": 2}
    assert get_top_items(counts, 5) == [("c", 2), ("a", 1), ("b", 1)]


def test_top_n_limits_result() -> None:
    counts = {"a": 3, "b": 2, "c": 1}
    assert get_top_items(counts, 2) == [("a", 3), ("b", 2)]


def test_unsupported_format_is_error(tmp_path: Path) -> None:
    path = write_file(tmp_path, "log.csv", CSV_TEXT)
    with pytest.raises(UnsupportedFormatError):
        analyze_files([path], "xml", False)
