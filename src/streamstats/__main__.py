"""Командная строка: python -m streamstats analyze ..."""

import argparse
import logging
import sys

from streamstats.analysis import analyze_files
from streamstats.constants import (
    EXIT_CODE_ERROR,
    EXIT_CODE_OK,
    LOG_FORMAT,
    REPORT_FORMATS,
    TOP_N,
)
from streamstats.errors import CliConfigError, StreamStatsError
from streamstats.filters import make_filters
from streamstats.report import build_report, print_report, save_report


def build_parser() -> argparse.ArgumentParser:
    """Создаёт разборщик аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="streamstats",
        description="Потоковый анализатор файлов с событиями (CSV и JSONL)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="посчитать статистику")
    analyze.add_argument("inputs", nargs="+", metavar="INPUT", help="входные файлы")
    analyze.add_argument(
        "--format",
        dest="file_format",
        help="csv или jsonl (если не указан - берётся из расширения файла)",
    )
    analyze.add_argument("--output", help="файл для JSON-отчёта (иначе - на экран)")
    analyze.add_argument(
        "--skip-invalid",
        action="store_true",
        help="пропускать плохие строки вместо остановки",
    )
    analyze.add_argument(
        "--top", type=int, default=TOP_N, help="сколько источников ошибок показать"
    )
    analyze.add_argument(
        "--report-format",
        choices=REPORT_FORMATS,
        help="формат отчёта (если не указан - по расширению --output, иначе json)",
    )
    analyze.add_argument(
        "--level", action="append", help="учитывать только этот уровень"
    )
    analyze.add_argument(
        "--source", action="append", help="учитывать только этот источник"
    )
    analyze.add_argument("--since", help="учитывать события не раньше (ISO 8601)")
    analyze.add_argument("--until", help="учитывать события не позже (ISO 8601)")
    return parser


def choose_report_format(args: argparse.Namespace) -> str:
    """Выбирает формат отчёта: явный --report-format, иначе по расширению."""
    if args.report_format is not None:
        return str(args.report_format)
    if args.output is not None and args.output.lower().endswith(".csv"):
        return "csv"
    return "json"


def run_analyze(args: argparse.Namespace) -> None:
    """Выполняет команду analyze."""
    if args.top < 1:
        raise CliConfigError("Параметр --top должен быть не меньше 1")
    filters = make_filters(args.level, args.source, args.since, args.until)
    stats = analyze_files(args.inputs, args.file_format, args.skip_invalid, filters)
    report = build_report(stats, args.top)
    report_format = choose_report_format(args)
    if args.output is None:
        print_report(report, report_format)
    else:
        save_report(report, args.output, report_format)
        print(f"Отчёт сохранён: {args.output}")


def main(argv: list[str] | None = None) -> int:
    """Точка входа. Возвращает код завершения (0 - успех, 2 - ошибка)."""
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    args = build_parser().parse_args(argv)


    try:
        run_analyze(args)
    except StreamStatsError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_CODE_ERROR
    except FileNotFoundError as error:
        print(f"Ошибка: файл или папка не найдены: {error.filename}", file=sys.stderr)
        return EXIT_CODE_ERROR
    except UnicodeDecodeError:
        print("Ошибка: файл должен быть в кодировке UTF-8", file=sys.stderr)
        return EXIT_CODE_ERROR
    except OSError as error:
        print(f"Ошибка ввода-вывода: {error}", file=sys.stderr)
        return EXIT_CODE_ERROR
    return EXIT_CODE_OK


if __name__ == "__main__":
    sys.exit(main())
