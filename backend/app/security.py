"""Small POC security guardrails.

These checks do not make the app production-secure. They only keep the local
demo from accepting messy identifiers or very large/nested client payloads.
"""

from __future__ import annotations

import math
import re
from typing import Any


SCHEMA_VERSION = "0.1.0"
SAFE_IDENTIFIER_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"
SCENARIO_IDENTIFIER_PATTERN = r"^[a-z0-9_]{1,80}$"
ACTION_TYPE_PATTERN = r"^[a-z][a-z0-9_]{0,63}$"

MAX_PAYLOAD_DEPTH = 4
MAX_PAYLOAD_KEYS = 20
MAX_PAYLOAD_LIST_ITEMS = 20
MAX_PAYLOAD_STRING_LENGTH = 500
MAX_PAYLOAD_TOTAL_NODES = 80

_SAFE_IDENTIFIER_RE = re.compile(SAFE_IDENTIFIER_PATTERN)
_SCENARIO_IDENTIFIER_RE = re.compile(SCENARIO_IDENTIFIER_PATTERN)
_ACTION_TYPE_RE = re.compile(ACTION_TYPE_PATTERN)


def ensure_safe_identifier(value: str, field_name: str) -> str:
    """Allow IDs that are safe for logs, URLs, and simple review output."""

    if not _SAFE_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(
            f"{field_name} must use 1-64 letters, numbers, underscores, or hyphens"
        )
    return value


def ensure_safe_scenario_id(value: str) -> str:
    """Allow checked-in scenario identifiers, not paths or arbitrary filenames."""

    if not _SCENARIO_IDENTIFIER_RE.fullmatch(value):
        raise ValueError("scenario_id must use 1-80 lowercase letters, numbers, or underscores")
    return value


def ensure_safe_action_type(value: str) -> str:
    """Allow simple action names like assess_scene or open_door."""

    if not _ACTION_TYPE_RE.fullmatch(value):
        raise ValueError(
            "action_type must start with a lowercase letter and use lowercase letters, "
            "numbers, or underscores"
        )
    return value


def ensure_safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Keep optional client payloads small and JSON-shaped.

    The current scenario does not need payload data, but the contract allows it
    for future manual/stubbed input. This prevents payloads from becoming a
    hidden place for giant blobs or surprising Python objects.
    """

    counter = _NodeCounter()
    _check_payload_value(payload, field_path="payload", depth=0, counter=counter)
    return payload


class _NodeCounter:
    def __init__(self) -> None:
        self.count = 0

    def add(self, field_path: str) -> None:
        self.count += 1
        if self.count > MAX_PAYLOAD_TOTAL_NODES:
            raise ValueError(f"{field_path} exceeds the payload node limit")


def _check_payload_value(
    value: Any,
    *,
    field_path: str,
    depth: int,
    counter: _NodeCounter,
) -> None:
    counter.add(field_path)
    if depth > MAX_PAYLOAD_DEPTH:
        raise ValueError(f"{field_path} is nested too deeply")

    if isinstance(value, dict):
        if len(value) > MAX_PAYLOAD_KEYS:
            raise ValueError(f"{field_path} has too many keys")
        for key, nested_value in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{field_path} contains a non-string key")
            if len(key) > 64:
                raise ValueError(f"{field_path}.{key[:16]}... has a key that is too long")
            _check_payload_value(
                nested_value,
                field_path=f"{field_path}.{key}",
                depth=depth + 1,
                counter=counter,
            )
        return

    if isinstance(value, list):
        if len(value) > MAX_PAYLOAD_LIST_ITEMS:
            raise ValueError(f"{field_path} has too many list items")
        for index, nested_value in enumerate(value):
            _check_payload_value(
                nested_value,
                field_path=f"{field_path}[{index}]",
                depth=depth + 1,
                counter=counter,
            )
        return

    if isinstance(value, str):
        if len(value) > MAX_PAYLOAD_STRING_LENGTH:
            raise ValueError(f"{field_path} string is too long")
        return

    if isinstance(value, bool) or value is None:
        return

    if isinstance(value, int):
        return

    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{field_path} must be a finite number")
        return

    raise ValueError(f"{field_path} must contain only JSON-style values")

