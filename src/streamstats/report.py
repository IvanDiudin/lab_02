"""Формирование отчёта: считаем ОДИН раз, записываем в JSON или CSV."""

import csv
import json
import sys
from collections.abc import Callable
from typing import Any, TextIO

from streamstats.analysis import get_top_items
from streamstats.constants import (
    CSV_WRITE_ENCODING,
    LEVELS,
    TOP_N,
    WRITE_ENCODING,
)


def build_report(stats: dict[str, Any], top_n: int = TOP_N) -> dict[str, Any]:
    """Собирает словарь-отчёт из статистики. Все расчёты только здесь."""
    levels = {}
    for level in LEVELS:
        levels[level] = stats["levels"].get(level, 0)

    top_errors = []
    for source, count in get_top_items(stats["error_sources"], top_n):
        top_errors.append({"source": source, "count": count})

    first = None
    if stats["first_timestamp"] is not None:
        first = stats["first_timestamp"].isoformat()
    last = None
    if stats["last_timestamp"] is not None:
        last = stats["last_timestamp"].isoformat()

    return {
        "total_events": stats["total"],
        "skipped_lines": stats["skipped"],
        "filtered_out": stats["filtered"],
        "events_by_level": levels,
        "events_by_source": dict(sorted(stats["sources"].items())),
        "top_error_sources": top_errors,
        "first_timestamp": first,
        "last_timestamp": last,
    }


def write_json(report: dict[str, Any], file: TextIO) -> None:
    """Записывает готовый отчёт в формате JSON."""
    json.dump(report, file, ensure_ascii=False, indent=2)
    file.write("\n")


def report_to_rows(report: dict[str, Any]) -> list[list[str]]:
    """Превращает готовый отчёт в таблицу из строк. Ничего заново не считает."""
    rows = [["section", "key", "value"]]
    rows.append(["total", "total_events", str(report["total_events"])])
    rows.append(["total", "skipped_lines", str(report["skipped_lines"])])
    rows.append(["total", "filtered_out", str(report["filtered_out"])])
    for level, count in report["events_by_level"].items():
        rows.append(["level", level, str(count)])
    for source, count in report["events_by_source"].items():
        rows.append(["source", source, str(count)])
    for item in report["top_error_sources"]:
        rows.append(["top_error_source", item["source"], str(item["count"])])
    rows.append(["time", "first_timestamp", report["first_timestamp"] or ""])
    rows.append(["time", "last_timestamp", report["last_timestamp"] or ""])
    return rows


def write_csv(report: dict[str, Any], file: TextIO) -> None:
    """Записывает готовый отчёт в формате CSV."""
    writer = csv.writer(file, lineterminator="\n")
    writer.writerows(report_to_rows(report))


REPORT_WRITERS: dict[str, Callable[[dict[str, Any], TextIO], None]] = {
    "json": write_json,
    "csv": write_csv,
}


def save_report(report: dict[str, Any], path: str, report_format: str = "json") -> None:
    """Сохраняет отчёт в файл в выбранном формате."""
    encoding = WRITE_ENCODING
    if report_format == "csv":
        encoding = CSV_WRITE_ENCODING
    with open(path, "w", encoding=encoding, newline="") as file_out:
        REPORT_WRITERS[report_format](report, file_out)


def print_report(report: dict[str, Any], report_format: str = "json") -> None:
    """Печатает отчёт на экран."""
    REPORT_WRITERS[report_format](report, sys.stdout)
