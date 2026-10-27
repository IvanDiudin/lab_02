"""Проверка (валидация) события. Само событие хранится в обычном словаре."""

from datetime import datetime, timezone
from typing import Any

from streamstats.constants import LEVELS, REQUIRED_FIELDS
from streamstats.errors import InvalidEventError, InvalidTimestampError


def parse_timestamp(text: str, place: str) -> datetime:
    """Превращает строку ISO 8601 в дату или кидает InvalidTimestampError."""
    fixed_text = text.strip()
    if fixed_text.endswith("Z"):
        fixed_text = fixed_text[:-1] + "+00:00"
    try:
        moment = datetime.fromisoformat(fixed_text)
    except ValueError:
        raise InvalidTimestampError(
            f"{place}: неверное значение поля 'timestamp': '{text}'"
        )
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment


def make_event(data: dict[str, Any], place: str) -> dict[str, Any]:
    """Проверяет словарь с данными и возвращает событие."""
    for field_name in REQUIRED_FIELDS:
        value = data.get(field_name)
        if not isinstance(value, str):
            raise InvalidEventError(
                f"{place}: нет поля '{field_name}' или оно не строка"
            )

    level = data["level"]
    if level not in LEVELS:
        raise InvalidEventError(f"{place}: неизвестный уровень '{level}'")

    if data["source"].strip() == "":
        raise InvalidEventError(f"{place}: поле 'source' пустое")

    moment = parse_timestamp(data["timestamp"], place)

    return {
        "timestamp": moment,
        "level": level,
        "source": data["source"],
        "message": data["message"],
    }
