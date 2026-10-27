# Лабораторная работа 2. Потоковый анализатор файлов

Пакет `streamstats` читает события из CSV и JSONL и строит JSON-отчёт.

## Установка

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (Linux/macOS: source .venv/bin/activate)
pip install -e ".[dev]"
```

## Запуск

```bash
python -m streamstats analyze logs.csv --format csv --output report.json
python -m streamstats analyze a.csv b.jsonl --output report.json
python -m streamstats analyze logs.jsonl --skip-invalid
python -m streamstats analyze logs.csv --top 10
python -m streamstats analyze logs.csv --output report.csv
python -m streamstats analyze logs.csv --level ERROR --level CRITICAL --since 2024-01-01T10:00:00
```

Параметры:
- `INPUT ...` - один или несколько файлов;
- `--format csv|jsonl` - формат (если не указан, берётся из расширения);
- `--output FILE` - куда сохранить отчёт (иначе печатается на экран);
- `--skip-invalid` - пропускать плохие строки;
- `--top N` - сколько источников ошибок показать (по умолчанию 5);
- `--report-format json|csv` - формат отчёта (если не указан: по расширению
  `--output`, иначе json);
- `--level L`, `--source S` - учитывать только эти уровни / источники
  (можно повторять);
- `--since T`, `--until T` - учитывать события только в этом интервале времени.

## Дополнительные задания

- **Реестр parser-функций.** Словарь `LINE_PARSERS` в `parsers.py`:
  название формата (= расширение файла) -> функция, которая разбирает одну
  строку. Свой формат добавляется так:
  `register_line_parser("semi", parse_semicolon)`. Встроенный пример - формат
  `pipe` (`timestamp|level|source|message`, файлы `.pipe`).
- **Фильтры** (`filters.py`). Каждое событие проверяется сразу после чтения,
  ничего не накапливается. Отфильтрованные события считаются в `filtered_out`.
- **CSV-отчёт без дублирования расчётов.** `build_report` считает всё один
  раз, дальше словарь `REPORT_WRITERS` выбирает, как записать готовый отчёт:
  `write_json` или `write_csv`.
- **Измерение памяти** на файле 500 МБ: `python scripts/measure_memory.py`
  (для быстрой проверки: `--size-mb 50`).

## Формат события

| поле | описание |
|------|----------|
| timestamp | время в формате ISO 8601 |
| level | DEBUG, INFO, WARNING, ERROR или CRITICAL |
| source | непустая строка |
| message | строка (может быть пустой) |

## Обработка ошибок

- По умолчанию: на первой плохой строке программа останавливается,
  печатает файл и номер строки, код завершения `2`.
- `--skip-invalid`: плохая строка пропускается, в лог пишется WARNING,
  число пропущенных строк попадает в отчёт (`skipped_lines`).
- Пустые строки в JSONL не считаются событиями и пропускаются молча.

## Память

Файл читается построчно (`for line in file`). Каждое событие сразу
учитывается в счётчиках и забывается. Хранятся только счётчики, поэтому
память зависит от числа разных источников, а не от размера файла.

## Проверка

```bash
python -m pytest
ruff check .
python -m streamstats --help
```
