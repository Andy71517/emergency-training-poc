"""Internal deterministic scenario definitions."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TransitionRule:
    rule_id: str
    when: dict[str, Any]
    updates: dict[str, Any]


@dataclass(frozen=True)
class EndCondition:
    expected_state: dict[str, Any]
    label: str


@dataclass(frozen=True)
class ScenarioDefinition:
    scenario_id: str
    title: str
    version: str
    initial_state: dict[str, Any]
    allowed_actions: tuple[str, ...]
    transition_rules: tuple[TransitionRule, ...]
    end_conditions: tuple[EndCondition, ...]
    expected_happy_path: tuple[str, ...]


@dataclass(frozen=True)
class TransitionCandidate:
    state: dict[str, Any]
    applied_transition_id: str | None
    note: str | None = None
