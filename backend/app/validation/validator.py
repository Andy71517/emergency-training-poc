"""Evaluate deterministic software rules for the toy scenario."""

from typing import Any

from backend.app.models.events import TraineeActionEvent
from backend.app.scenario_engine.models import ScenarioDefinition
from backend.app.scenario_engine.state_paths import MISSING, get_path
from backend.app.validation.models import (
    ValidationEvaluation,
    ValidationFinding,
    ValidationResult,
)
from backend.app.validation.rules import RuleDefinition


class ScenarioValidator:
    """Checks fixture rule conformance; it provides no real-world protocol authority."""

    def __init__(self, scenario: ScenarioDefinition, rules: tuple[RuleDefinition, ...]) -> None:
        self.scenario = scenario
        self.rules = rules

    def evaluate(
        self,
        event: TraineeActionEvent,
        current_state: dict[str, Any],
        candidate_state: dict[str, Any],
        transition_note: str | None = None,
    ) -> ValidationEvaluation:
        warnings: list[ValidationFinding] = []
        errors: list[ValidationFinding] = []
        notes: list[str] = []
        applied: list[str] = []
        blocks = False

        for rule in self.rules:
            if self._matches(rule, event, current_state):
                finding = ValidationFinding(
                    code=rule.code,
                    message=rule.message,
                    rule_id=rule.rule_id,
                    instructor_note=rule.instructor_note,
                )
                (errors if rule.severity == "error" else warnings).append(finding)
                applied.append(rule.rule_id)
                blocks = blocks or rule.blocks_transition

        state_errors = self._state_bounds_findings(candidate_state)
        if state_errors:
            errors.extend(state_errors)
            blocks = True

        if (
            transition_note
            and event.action_type in self.scenario.allowed_actions
            and not errors
            and not applied
        ):
            warnings.append(
                ValidationFinding(
                    code="no_matching_transition",
                    message=transition_note,
                    rule_id="scenario-transition-match",
                )
            )

        if not applied:
            notes.append("No scenario-specific conformance rule was triggered.")

        status = "error" if errors else "warning" if warnings else "ok"
        result = ValidationResult(
            session_id=event.session_id,
            scenario_id=event.scenario_id,
            event_id=event.event_id,
            timestamp=event.timestamp,
            sequence_number=event.sequence_number,
            status=status,
            warnings=warnings,
            errors=errors,
            notes=notes,
            applied_rule_ids=applied,
        )
        return ValidationEvaluation(result=result, blocks_transition=blocks)

    def _matches(
        self,
        rule: RuleDefinition,
        event: TraineeActionEvent,
        state: dict[str, Any],
    ) -> bool:
        for key, expected in rule.when.items():
            if key == "action_type_not_in_scenario_allowed_actions":
                if bool(expected) != (event.action_type not in self.scenario.allowed_actions):
                    return False
            elif key == "action_type":
                if event.action_type != expected:
                    return False
            elif key == "action_type_in":
                if event.action_type not in expected:
                    return False
            elif key == "state.phase_not":
                if state.get("phase") == expected:
                    return False
            elif key.startswith("state."):
                if get_path(state, key.removeprefix("state."), MISSING) != expected:
                    return False
            elif key == "any_state_equals":
                if not any(get_path(state, name, MISSING) == value for name, value in expected.items()):
                    return False
            elif key == "minimum_sequence_number":
                if event.sequence_number >= int(expected):
                    return False
            elif key == "maximum_sequence_number":
                if event.sequence_number <= int(expected):
                    return False
            else:
                return False
        return True

    def _state_bounds_findings(self, state: dict[str, Any]) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        for key, initial_value in self.scenario.initial_state.items():
            if key not in state or type(state.get(key)) is not type(initial_value):
                findings.append(
                    ValidationFinding(
                        code="invalid_state_shape",
                        message=f"State field '{key}' is missing or has an invalid type.",
                        rule_id="state-bounds",
                    )
                )
        if state.get("scenario_outcome") not in {"in_progress", "completed", "stopped"}:
            findings.append(
                ValidationFinding(
                    code="invalid_scenario_outcome",
                    message="Scenario outcome is outside the POC state bounds.",
                    rule_id="state-bounds",
                )
            )
        return findings
