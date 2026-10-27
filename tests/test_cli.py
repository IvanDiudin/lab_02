"""Integration-тесты командной строки (с временным каталогом)."""

import json
from pathlib import Path

import pytest

from streamstats.__main__ import main
from tests.helpers import CSV_TEXT, GOOD_LINE, JSONL_TEXT, write_file


def test_cli_writes_report(tmp_path: Path) -> None:
    source = write_file(tmp_path, "log.csv", CSV_TEXT)
    output = str(tmp_path / "report.json")
    code = main(["analyze", source, "--format", "csv", "--output", output])
    assert code == 0
    report = json.loads(Path(output).read_text(encoding="utf-8"))
    assert report["total_events"] == 4


def test_cli_merges_several_files(tmp_path: Path) -> None:
    first = write_file(tmp_path, "a.csv", CSV_TEXT)
    second = write_file(tmp_path, "b.jsonl", JSONL_TEXT)
    output = str(tmp_path / "report.json")
    assert main(["analyze", first, second, "--output", output]) == 0
    report = json.loads(Path(output).read_text(encoding="utf-8"))
    assert report["total_events"] == 8


def test_cli_stops_on_bad_line_with_code_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    text = GOOD_LINE + "\n" + GOOD_LINE + "\n{сломано\n"
    source = write_file(tmp_path, "bad.jsonl", text)
    output = tmp_path / "report.json"
    code = main(["analyze", source, "--output", str(output)])
    assert code == 2
    error_text = capsys.readouterr().err
    assert "строка 3" in error_text
    assert "bad.jsonl" in error_text
    assert not output.exists()


def test_cli_skip_invalid_counts_good_lines(tmp_path: Path) -> None:
    text = GOOD_LINE + "\n{сломано\n" + GOOD_LINE + "\n"
    source = write_file(tmp_path, "bad.jsonl", text)
    output = str(tmp_path / "report.json")
    code = main(["analyze", source, "--skip-invalid", "--output", output])
    assert code == 0
    report = json.loads(Path(output).read_text(encoding="utf-8"))
    assert report["total_events"] == 2
    assert report["skipped_lines"] == 1


def test_cli_keeps_cyrillic_in_report(tmp_path: Path) -> None:
    line = GOOD_LINE.replace("web", "сервер")
    source = write_file(tmp_path, "ru.jsonl", line + "\n")
    output = tmp_path / "report.json"
    assert main(["analyze", source, "--output", str(output)]) == 0
    assert "сервер" in output.read_text(encoding="utf-8")


def test_cli_does_not_change_input_file(tmp_path: Path) -> None:
    source = write_file(tmp_path, "log.csv", CSV_TEXT)
    before = Path(source).read_bytes()
    main(["analyze", source, "--output", str(tmp_path / "r.json")])
    assert Path(source).read_bytes() == before


def test_cli_missing_file_gives_code_2(tmp_path: Path) -> None:
    assert main(["analyze", str(tmp_path / "no_such.csv")]) == 2


def test_cli_unknown_extension_gives_code_2(tmp_path: Path) -> None:
    source = write_file(tmp_path, "log.txt", CSV_TEXT)
    assert main(["analyze", source]) == 2


def test_cli_wrong_top_gives_code_2(tmp_path: Path) -> None:
    source = write_file(tmp_path, "log.csv", CSV_TEXT)
    assert main(["analyze", source, "--top", "0"]) == 2


def test_cli_prints_report_without_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = write_file(tmp_path, "log.csv", CSV_TEXT)
    assert main(["analyze", source]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["total_events"] == 4
