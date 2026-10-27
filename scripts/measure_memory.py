"""Измерение памяти: анализ файла не меньше 500 МБ.

Запуск:  python scripts/measure_memory.py
Меньший файл для быстрой проверки:  python scripts/measure_memory.py --size-mb 50
"""

import argparse
import os
import tempfile
import time
import tracemalloc

from streamstats.analysis import analyze_files

LEVEL_NAMES = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
SOURCES_COUNT = 100
MEGABYTE = 1024 * 1024


def make_line(number: int) -> str:
    """Возвращает одну строку JSONL с номером number."""
    seconds = number % 60
    minutes = (number // 60) % 60
    hours = (number // 3600) % 24
    day = 1 + (number // 86400) % 28
    level = LEVEL_NAMES[number % 5]
    source = f"service_{number % SOURCES_COUNT}"
    moment = f"2024-01-{day:02d}T{hours:02d}:{minutes:02d}:{seconds:02d}"
    return (
        f'{{"timestamp": "{moment}", "level": "{level}", '
        f'"source": "{source}", "message": "Сообщение номер {number}"}}\n'
    )


def generate_file(path: str, size_mb: int) -> int:
    """Записывает файл JSONL нужного размера и возвращает число строк."""
    target_bytes = size_mb * MEGABYTE
    written = 0
    number = 0
    with open(path, "w", encoding="utf-8") as file:
        while written < target_bytes:
            line = make_line(number)
            file.write(line)
            written += len(line.encode("utf-8"))
            number += 1
    return number


def main() -> None:
    """Создаёт большой файл, анализирует его и печатает пик памяти."""
    parser = argparse.ArgumentParser(description="Измерение памяти streamstats")
    parser.add_argument("--size-mb", type=int, default=500, help="размер файла, МБ")
    args = parser.parse_args()

    folder = tempfile.mkdtemp()
    path = os.path.join(folder, "big.jsonl")
    try:
        print(f"Создаю файл {args.size_mb} МБ...")
        lines = generate_file(path, args.size_mb)
        real_size = os.path.getsize(path) / MEGABYTE
        print(f"Готово: {lines} строк, {real_size:.1f} МБ")

        print("Анализирую...")
        tracemalloc.start()
        started = time.time()
        stats = analyze_files([path], "jsonl", False)
        spent = time.time() - started
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"Событий учтено: {stats['total']}")
        print(f"Время: {spent:.1f} с")
        print(f"Размер файла: {real_size:.1f} МБ")
        print(f"Пик памяти Python: {peak / MEGABYTE:.2f} МБ")
    finally:
        if os.path.exists(path):
            os.remove(path)
        os.rmdir(folder)


if __name__ == "__main__":
    main()
