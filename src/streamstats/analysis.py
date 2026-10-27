"""Чтение файлов по строкам и подсчёт статистики.

События не хранятся: каждая запись прочитана, учтена в счётчиках и забыта.
"""

import csv
import logging
from datetime import datetime
from typing import Any

from streamstats.constants import ERROR_LEVELS, READ_ENCODING
from streamstats.errors import StreamStatsError, UnsupportedFormatError
from streamstats.filters import event_matches, make_filters
from streamstats.parsers import (
    LINE_PARSERS,
    LineParser,
    detect_format,
    parse_csv_row,
)

logger = logging.getLogger(__name__)


def make_stats() -> dict[str, Any]:
    """Создаёт пустую статистику (словарь со счётчиками)."""
    return {
        "total": 0,
        "skipped": 0,
        "filtered": 0,
        "levels": {},
        "sources": {},
        "error_sources": {},
        "first_timestamp": None,
        "last_timestamp": None,
    }


def add_one(counts: dict[str, int], key: str) -> None:
    """Увеличивает счётчик key на 1 (если ключа ещё нет - начинаем с 0)."""
    counts[key] = counts.get(key, 0) + 1


def update_stats(stats: dict[str, Any], event: dict[str, Any]) -> None:
    """Учитывает одно событие в статистике."""
    stats["total"] += 1
    add_one(stats["levels"], event["level"])
    add_one(stats["sources"], event["source"])
    if event["level"] in ERROR_LEVELS:
        add_one(stats["error_sources"], event["source"])

    moment: datetime = event["timestamp"]
    if stats["first_timestamp"] is None or moment < stats["first_timestamp"]:
        stats["first_timestamp"] = moment
    if stats["last_timestamp"] is None or moment > stats["last_timestamp"]:
        stats["last_timestamp"] = moment


def take_event(
    stats: dict[str, Any], event: dict[str, Any], filters: dict[str, Any]
) -> None:
    """Учитывает событие, если оно проходит фильтры. Иначе просто считает его."""
    if event_matches(event, filters):
        update_stats(stats, event)
    else:
        stats["filtered"] += 1


def handle_bad_line(
    stats: dict[str, Any], error: StreamStatsError, skip_invalid: bool
) -> None:
    """Режим по умолчанию - останавливаемся. С --skip-invalid - пропускаем."""
    if not skip_invalid:
        raise error
    logger.warning("Строка пропущена. %s", error)
    stats["skipped"] += 1


def process_csv_file(
    path: str, stats: dict[str, Any], skip_invalid: bool, filters: dict[str, Any]
) -> None:
    """Читает CSV с заголовком построчно и добавляет события в статистику."""
    with open(path, encoding=READ_ENCODING, newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            place = f"{path}, строка {reader.line_num}"
            try:
                event = parse_csv_row(row, place)
            except StreamStatsError as error:
                handle_bad_line(stats, error, skip_invalid)
                continue
            take_event(stats, event, filters)


def process_line_file(
    path: str,
    parser: LineParser,
    stats: dict[str, Any],
    skip_invalid: bool,
    filters: dict[str, Any],
) -> None:
    """Читает построчный формат (JSONL, pipe, свой) и считает события.

    parser - функция из реестра LINE_PARSERS: она разбирает одну строку.
    """
    with open(path, encoding=READ_ENCODING) as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if line == "":
                continue
            place = f"{path}, строка {line_number}"
            try:
                event = parser(line, place)
            except StreamStatsError as error:
                handle_bad_line(stats, error, skip_invalid)
                continue
            take_event(stats, event, filters)


def analyze_files(
    paths: list[str],
    file_format: str | None,
    skip_invalid: bool,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Читает все файлы по очереди и считает общую статистику."""
    if filters is None:
        filters = make_filters()
    stats = make_stats()
    for path in paths:
        if file_format is None:
            current_format = detect_format(path)
        else:
            current_format = file_format
        logger.info("Обработка файла %s (формат %s)", path, current_format)

        if current_format == "csv":
            process_csv_file(path, stats, skip_invalid, filters)
        elif current_format in LINE_PARSERS:
            parser = LINE_PARSERS[current_format]
            process_line_file(path, parser, stats, skip_invalid, filters)
        else:
            raise UnsupportedFormatError(f"Неподдерживаемый формат: {current_format}")
    return stats


def get_top_items(counts: dict[str, int], n: int) -> list[tuple[str, int]]:
    """Возвращает n самых частых элементов. Порядок всегда одинаковый."""
    pairs: list[tuple[int, str]] = []
    for name, count in counts.items():
        pairs.append((-count, name))
    pairs.sort()

    top: list[tuple[str, int]] = []
    for minus_count, name in pairs[:n]:
        top.append((name, -minus_count))
    return top
