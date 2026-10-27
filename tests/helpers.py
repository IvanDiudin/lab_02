"""Общие данные и функции для тестов."""

import json
from pathlib import Path


def make_json_line(timestamp: str, level: str, source: str, message: str) -> str:
    """Собирает одну строку JSONL (кириллица остаётся буквами)."""
    event = {
        "timestamp": timestamp,
        "level": level,
        "source": source,
        "message": message,
    }
    return json.dumps(event, ensure_ascii=False)


CSV_TEXT = (
    "timestamp,level,source,message\n"
    "2024-01-01T10:00:00,INFO,web,Запуск сервера\n"
    "2024-01-01T10:05:00,ERROR,db,Ошибка подключения\n"
    "2024-01-01T10:10:00,CRITICAL,db,Диск переполнен\n"
    "2024-01-01T10:15:00,ERROR,web,Таймаут\n"
)

JSONL_TEXT = (
    "\n".join(
        [
            make_json_line("2024-01-01T10:00:00", "INFO", "web", "Запуск сервера"),
            make_json_line("2024-01-01T10:05:00", "ERROR", "db", "Ошибка подключения"),
            make_json_line("2024-01-01T10:10:00", "CRITICAL", "db", "Диск переполнен"),
            make_json_line("2024-01-01T10:15:00", "ERROR", "web", "Таймаут"),
        ]
    )
    + "\n"
)

GOOD_LINE = make_json_line("2024-01-01T10:00:00", "INFO", "web", "ok")


def write_file(folder: Path, name: str, text: str) -> str:
    """Создаёт файл во временной папке и возвращает путь к нему."""
    path = folder / name
    path.write_text(text, encoding="utf-8")
    return str(path)
