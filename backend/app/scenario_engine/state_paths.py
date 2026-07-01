"""Small helpers for dotted paths inside deterministic scenario state."""

from copy import deepcopy
from typing import Any


MISSING = object()


def get_path(state: dict[str, Any], path: str, default: Any = MISSING) -> Any:
    current: Any = state
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            if default is MISSING:
                raise KeyError(path)
            return default
        current = current[part]
    return current


def set_path(state: dict[str, Any], path: str, value: Any) -> None:
    current: dict[str, Any] = state
    parts = path.split(".")
    for part in parts[:-1]:
        next_value = current.get(part)
        if not isinstance(next_value, dict):
            next_value = {}
            current[part] = next_value
        current = next_value
    current[parts[-1]] = deepcopy(value)
