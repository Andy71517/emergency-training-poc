"""Structured POC rule-conformance results."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ValidationFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    rule_id: str | None = None


class ValidationResult(BaseModel):
    """A software rule result, not a clinical or operational judgment."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "0.1.0"
    session_id: str
    scenario_id: str
    event_id: str
    timestamp: datetime
    sequence_number: int = Field(ge=1)
    status: Literal["ok", "warning", "error"]
    warnings: list[ValidationFinding] = Field(default_factory=list)
    errors: list[ValidationFinding] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    applied_rule_ids: list[str] = Field(default_factory=list)


class ValidationEvaluation(BaseModel):
    result: ValidationResult
    blocks_transition: bool = False
