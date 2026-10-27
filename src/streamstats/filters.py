"""Фильтры событий по уровню, источнику и времени.

Фильтр проверяет каждое событие сразу, как оно прочитано, и ничего не копит.
"""

from typing import Any

from streamstats.constants import LEVELS
from streamstats.errors import CliConfigError
from streamstats.models import parse_timestamp


def make_filters(
    levels: list[str] | None = None,
    sources: list[str] | None = None,
    since: str | None = None,
    until: str | None = None,
) -> dict[str, Any]:
    """Собирает фильтры в словарь. None значит "этот фильтр не используется"."""
    if levels is not None:
        for level in levels:
            if level not in LEVELS:
                raise CliConfigError(f"Неизвестный уровень в --level: '{level}'")

    since_moment = None
    if since is not None:
        since_moment = parse_timestamp(since, "--since")
    until_moment = None
    if until is not None:
        until_moment = parse_timestamp(until, "--until")

    return {
        "levels": levels,
        "sources": sources,
        "since": since_moment,
        "until": until_moment,
    }


def event_matches(event: dict[str, Any], filters: dict[str, Any]) -> bool:
    """True, если событие проходит все включённые фильтры."""
    if filters["levels"] is not None and event["level"] not in filters["levels"]:
        return False
    if filters["sources"] is not None and event["source"] not in filters["sources"]:
        return False
    if filters["since"] is not None and event["timestamp"] < filters["since"]:
        return False
    return not (filters["until"] is not None and event["timestamp"] > filters["until"])
