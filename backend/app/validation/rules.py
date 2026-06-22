"""Load declarative POC conformance rules from YAML."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RULE_DIRECTORY = REPOSITORY_ROOT / "validation" / "rules"


@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    severity: str
    when: dict[str, Any]
    code: str
    message: str
    blocks_transition: bool


def load_rules(
    scenario_id: str,
    rule_directory: Path = DEFAULT_RULE_DIRECTORY,
) -> tuple[RuleDefinition, ...]:
    path = (rule_directory / f"{scenario_id}_rules.yaml").resolve()
    if path.parent != rule_directory.resolve() or not path.is_file():
        raise ValueError(f"Rule file not found for scenario: {scenario_id}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("scenario_id") != scenario_id:
        raise ValueError("Rule file scenario identifier mismatch")
    return tuple(
        RuleDefinition(
            rule_id=item["id"],
            severity=item["severity"],
            when=dict(item["when"]),
            code=item["result"]["code"],
            message=item["result"]["message"],
            blocks_transition=bool(item["result"].get("blocks_transition", False)),
        )
        for item in data.get("rules", [])
    )
