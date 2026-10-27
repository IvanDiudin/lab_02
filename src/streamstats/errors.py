"""Свои исключения проекта."""


class StreamStatsError(Exception):
    """Базовая ошибка. Все остальные ошибки проекта наследуются от неё."""


class UnsupportedFormatError(StreamStatsError):
    """Формат файла не поддерживается (не csv и не jsonl)."""


class InvalidEventError(StreamStatsError):
    """Неверное событие: нет поля, плохой уровень, сломанный JSON и т.д."""


class InvalidTimestampError(StreamStatsError):
    """Временная метка не соответствует формату ISO 8601."""


class CliConfigError(StreamStatsError):
    """Неверные параметры командной строки."""
