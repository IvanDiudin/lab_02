"""Все константы проекта."""

LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

ERROR_LEVELS = ("ERROR", "CRITICAL")

REQUIRED_FIELDS = ("timestamp", "level", "source", "message")

TOP_N = 5

EXIT_CODE_OK = 0
EXIT_CODE_ERROR = 2

READ_ENCODING = "utf-8-sig"
WRITE_ENCODING = "utf-8"

LOG_FORMAT = "%(levelname)s: %(message)s"

REPORT_FORMATS = ("json", "csv")
CSV_WRITE_ENCODING = "utf-8-sig"
