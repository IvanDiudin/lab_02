"""Тесты дополнительных заданий: реестр форматов, фильтры, CSV-отчёт."""

import csv
import json
from pathlib import Path

import pytest

from streamstats.__main__ import main
from streamstats.analysis import analyze_files
from streamstats.errors import CliConfigError, InvalidEventError, InvalidTimestampError
from streamstats.filters import event_matches, make_filters
from streamstats.models import make_event
from streamstats.parsers import (
    LINE_PARSERS,
    detect_format,
    parse_pipe_line,
    register_line_parser,
)
from streamstats.report import build_report, report_to_rows
from tests.helpers import CSV_TEXT, write_file

PIPE_TEXT = (
    "2024-01-01T10:00:00|INFO|web|Запуск | сервера\n"
    "2024-01-01T10:05:00|ERROR|db|Ошибка подключения\n"
)




def test_builtin_pipe_format_works(tmp_path: Path) -> None:
    path = write_file(tmp_path, "log.pipe", PIPE_TEXT)
    stats = analyze_files([path], None, False)
    assert stats["total"] == 2
    assert stats["levels"]["ERROR"] == 1


def test_pipe_line_may_contain_bar_in_message() -> None:
    event = parse_pipe_line(PIPE_TEXT.splitlines()[0], "x, строка 1")
    assert event["message"] == "Запуск | сервера"


def test_pipe_line_with_wrong_field_count_is_error() -> None:
    with pytest.raises(InvalidEventError, match="строка 3"):
        parse_pipe_line("только|два", "x, строка 3")


def test_user_can_register_own_format(tmp_path: Path) -> None:
    def parse_semicolon(line: str, place: str) -> dict[str, object]:
        timestamp, level, source, message = line.split(";")
        data = {
            "timestamp": timestamp,
            "level": level,
            "source": source,
            "message": message,
        }
        return make_event(data, place)

    register_line_parser("semi", parse_semicolon)
    try:
        path = write_file(tmp_path, "log.semi", "2024-01-01T10:00:00;INFO;web;ok\n")
        assert detect_format(path) == "semi"
        assert analyze_files([path], None, False)["total"] == 1
    finally:
        del LINE_PARSERS["semi"]



def make_event_for_filter(level: str, source: str, timestamp: str) -> dict[str, object]:
    data = {"timestamp": timestamp, "level": level, "source": source, "message": ""}
    return make_event(data, "test")


def test_empty_filters_pass_everything() -> None:
    event = make_event_for_filter("INFO", "web", "2024-01-01T10:00:00")
    assert event_matches(event, make_filters())


def test_level_and_source_filters() -> None:
    event = make_event_for_filter("INFO", "web", "2024-01-01T10:00:00")
    assert event_matches(event, make_filters(levels=["INFO", "ERROR"]))
    assert not event_matches(event, make_filters(levels=["ERROR"]))
    assert event_matches(event, make_filters(sources=["web"]))
    assert not event_matches(event, make_filters(sources=["db"]))


def test_time_filters() -> None:
    event = make_event_for_filter("INFO", "web", "2024-01-01T10:00:00")
    assert event_matches(event, make_filters(since="2024-01-01T09:00:00"))
    assert not event_matches(event, make_filters(since="2024-01-01T11:00:00"))
    assert event_matches(event, make_filters(until="2024-01-01T10:00:00"))
    assert not event_matches(event, make_filters(until="2024-01-01T09:00:00"))


def test_unknown_level_in_filter_is_error() -> None:
    with pytest.raises(CliConfigError):
        make_filters(levels=["NOTICE"])


def test_bad_time_in_filter_is_error() -> None:
    with pytest.raises(InvalidTimestampError, match="--since"):
        make_filters(since="вчера")


def test_filters_change_statistics(tmp_path: Path) -> None:
    path = write_file(tmp_path, "log.csv", CSV_TEXT)
    filters = make_filters(levels=["ERROR"], sources=["db"])
    stats = analyze_files([path], "csv", False, filters)
    assert stats["total"] == 1
    assert stats["filtered"] == 3
    assert stats["skipped"] == 0


def test_cli_filters(tmp_path: Path) -> None:
    source = write_file(tmp_path, "log.csv", CSV_TEXT)
    output = tmp_path / "report.json"
    code = main(
        ["analyze", source, "--level", "ERROR", "--level", "CRITICAL",
         "--since", "2024-01-01T10:07:00", "--output", str(output)]
    )
    assert code == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["total_events"] == 2
    assert report["filtered_out"] == 2


def test_cli_wrong_level_gives_code_2(tmp_path: Path) -> None:
    source = write_file(tmp_path, "log.csv", CSV_TEXT)
    assert main(["analyze", source, "--level", "NOTICE"]) == 2




def test_csv_report_is_built_from_same_report(tmp_path: Path) -> None:
    source = write_file(tmp_path, "log.csv", CSV_TEXT)
    report = build_report(analyze_files([source], "csv", False))
    rows = report_to_rows(report)
    assert rows[0] == ["section", "key", "value"]
    assert ["total", "total_events", "4"] in rows
    assert ["top_error_source", "db", "2"] in rows


def test_cli_writes_csv_report_by_extension(tmp_path: Path) -> None:
    source = write_file(tmp_path, "log.csv", CSV_TEXT.replace("web", "сервер"))
    output = tmp_path / "report.csv"
    assert main(["analyze", source, "--output", str(output)]) == 0
    with open(output, encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file))
    assert ["total", "total_events", "4"] in rows
    assert ["source", "сервер", "2"] in rows


def test_cli_report_format_csv_on_screen(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = write_file(tmp_path, "log.csv", CSV_TEXT)
    assert main(["analyze", source, "--report-format", "csv"]) == 0
    assert "total,total_events,4" in capsys.readouterr().out


def test_json_and_csv_reports_have_same_numbers(tmp_path: Path) -> None:
    source = write_file(tmp_path, "log.csv", CSV_TEXT)
    json_path = tmp_path / "r.json"
    csv_path = tmp_path / "r.csv"
    main(["analyze", source, "--output", str(json_path)])
    main(["analyze", source, "--output", str(csv_path)])
    from_json = json.loads(json_path.read_text(encoding="utf-8"))
    with open(csv_path, encoding="utf-8-sig", newline="") as file:
        from_csv = list(csv.reader(file))
    assert ["total", "total_events", str(from_json["total_events"])] in from_csv
