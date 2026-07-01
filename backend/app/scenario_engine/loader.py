"""Load small declarative scenario fixtures from YAML."""

from pathlib import Path
from typing import Any

import yaml

from backend.app.scenario_engine.models import EndCondition, ScenarioDefinition, TransitionRule
from backend.app.security import ensure_safe_scenario_id

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SCENARIO_DIRECTORY = REPOSITORY_ROOT / "scenarios"


class ScenarioLoadError(ValueError):
    pass


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ScenarioLoadError(f"Scenario file not found: {path.name}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ScenarioLoadError(f"Scenario must be a YAML object: {path.name}")
    return data


def load_scenario(
    scenario_id: str = "smoke_inhalation_room_v0",
    scenario_directory: Path = DEFAULT_SCENARIO_DIRECTORY,
) -> ScenarioDefinition:
    """Load a scenario by identifier without allowing path traversal."""

    try:
        ensure_safe_scenario_id(scenario_id)
    except ValueError as error:
        raise ScenarioLoadError(str(error)) from error
    path = (scenario_directory / f"{scenario_id}.yaml").resolve()
    if path.parent != scenario_directory.resolve():
        raise ScenarioLoadError("Invalid scenario identifier")
    data = _read_yaml(path)
    required = {
        "scenario_id",
        "title",
        "version",
        "initial_state",
        "allowed_actions",
        "transition_rules",
        "end_conditions",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise ScenarioLoadError(f"Scenario is missing fields: {', '.join(missing)}")
    if data["scenario_id"] != scenario_id:
        raise ScenarioLoadError("Scenario identifier does not match its filename")

    transitions = tuple(
        TransitionRule(
            rule_id=item["id"],
            when=dict(item["when"]),
            updates=dict(item.get("set", {})),
        )
        for item in data["transition_rules"]
    )
    end_conditions = tuple(
        EndCondition(expected_state=dict(item["state_equals"]), label=item["label"])
        for item in data["end_conditions"]
    )
    return ScenarioDefinition(
        scenario_id=data["scenario_id"],
        title=data["title"],
        version=str(data["version"]),
        initial_state=dict(data["initial_state"]),
        allowed_actions=tuple(data["allowed_actions"]),
        transition_rules=transitions,
        end_conditions=end_conditions,
        expected_happy_path=tuple(data.get("expected_happy_path", [])),
    )
