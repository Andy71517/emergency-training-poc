"""Pure deterministic state transition engine."""

from copy import deepcopy
from typing import Any

from backend.app.scenario_engine.models import ScenarioDefinition, TransitionCandidate


class ScenarioEngine:
    def __init__(self, scenario: ScenarioDefinition) -> None:
        self.scenario = scenario

    def initial_state(self) -> dict[str, Any]:
        return deepcopy(self.scenario.initial_state)

    def preview_action(self, state: dict[str, Any], action_type: str) -> TransitionCandidate:
        """Return a candidate without mutating the supplied authoritative state."""

        for rule in self.scenario.transition_rules:
            if self._matches(rule.when, state, action_type):
                candidate = deepcopy(state)
                candidate.update(deepcopy(rule.updates))
                return TransitionCandidate(candidate, rule.rule_id)
        return TransitionCandidate(
            deepcopy(state),
            None,
            f"No transition matched action '{action_type}' in the current state.",
        )

    def terminal_label(self, state: dict[str, Any]) -> str | None:
        for condition in self.scenario.end_conditions:
            if all(state.get(key) == value for key, value in condition.expected_state.items()):
                return condition.label
        return None

    def next_expected_actions(self, state: dict[str, Any]) -> list[str]:
        if self.terminal_label(state) is not None:
            return []
        actions: list[str] = []
        for rule in self.scenario.transition_rules:
            action = rule.when.get("action_type")
            if action and self._matches_state(rule.when, state) and action not in actions:
                actions.append(action)
        return actions

    @staticmethod
    def _matches(conditions: dict[str, Any], state: dict[str, Any], action_type: str) -> bool:
        expected_action = conditions.get("action_type")
        return (expected_action is None or expected_action == action_type) and ScenarioEngine._matches_state(
            conditions, state
        )

    @staticmethod
    def _matches_state(conditions: dict[str, Any], state: dict[str, Any]) -> bool:
        return all(
            key == "action_type" or state.get(key) == expected
            for key, expected in conditions.items()
        )
