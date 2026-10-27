"""Разбор ОДНОЙ записи."""

import json
from collections.abc import Callable
from typing import Any

from streamstats.errors import InvalidEventError, UnsupportedFormatError
from streamstats.models import make_event

LineParser = Callable[[str, str], dict[str, Any]]


def parse_csv_row(row: dict[str, Any], place: str) -> dict[str, Any]:
    """CSV: модуль csv уже превратил строку в словарь. Проверяем его."""
    return make_event(row, place)


def parse_jsonl_line(line: str, place: str) -> dict[str, Any]:
    """JSONL: превращает одну строку с JSON в событие."""
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        raise InvalidEventError(f"{place}: неверный JSON")
    if not isinstance(data, dict):
        raise InvalidEventError(f"{place}: ожидался JSON-объект")
    return make_event(data, place)


def parse_pipe_line(line: str, place: str) -> dict[str, Any]:
    """Пример своего формата: четыре поля через вертикальную черту.

    timestamp|level|source|message
    """
    parts = line.split("|", 3)
    if len(parts) != 4:
        raise InvalidEventError(f"{place}: ожидалось 4 поля через '|'")
    data = {
        "timestamp": parts[0],
        "level": parts[1],
        "source": parts[2],
        "message": parts[3],
    }
    return make_event(data, place)

LINE_PARSERS: dict[str, LineParser] = {
    "jsonl": parse_jsonl_line,
    "pipe": parse_pipe_line,
}


def register_line_parser(name: str, parser: LineParser) -> None:
    """Добавляет свой формат: после этого он работает без правок остального кода."""
    LINE_PARSERS[name] = parser


def detect_format(path: str) -> str:
    """Определяет формат файла по расширению."""
    lower_path = path.lower()
    if "." in lower_path:
        extension = lower_path.rsplit(".", 1)[1]
        if extension == "csv" or extension in LINE_PARSERS:
            return extension
    raise UnsupportedFormatError(
        f"Не удалось определить формат файла {path}, укажите --format"
    )
