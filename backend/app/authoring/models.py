"""Contracts for AI-suggested, instructor-controlled scenario drafts."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DraftStatus(StrEnum):
    SUGGESTED = "suggested"
    INSTRUCTOR_EDITED = "instructor_edited"
    APPROVED = "approved"
    REJECTED = "rejected"


class GenerationJobStatus(StrEnum):
    REVIEW_READY = "review_ready"


class ScenarioGenerationRequest(StrictModel):
    prompt: str = Field(min_length=10, max_length=2_000)
    requested_by: str = Field(default="local-instructor", min_length=1, max_length=100)


class ScenarioCue(StrictModel):
    cue_id: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=500)


class ScenarioActionOption(StrictModel):
    action_id: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=160)
    intended_effect: str = Field(min_length=1, max_length=500)


class ScenarioTransitionDraft(StrictModel):
    transition_id: str = Field(min_length=1, max_length=80)
    when: str = Field(min_length=1, max_length=500)
    then: str = Field(min_length=1, max_length=500)


class ScenarioAssetRequest(StrictModel):
    asset_id: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=160)
    purpose: str = Field(min_length=1, max_length=500)
    physics_intent: str = Field(min_length=1, max_length=500)


class ScenarioDraftContent(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=1_000)
    training_goals: list[str] = Field(min_length=1, max_length=20)
    environment: str = Field(min_length=1, max_length=1_000)
    difficulty: str = Field(min_length=1, max_length=100)
    estimated_duration_minutes: int = Field(ge=1, le=240)
    occupants: list[str] = Field(default_factory=list, max_length=30)
    cues: list[ScenarioCue] = Field(default_factory=list, max_length=50)
    actions: list[ScenarioActionOption] = Field(default_factory=list, max_length=100)
    transitions: list[ScenarioTransitionDraft] = Field(default_factory=list, max_length=100)
    end_conditions: list[str] = Field(min_length=1, max_length=30)
    assets: list[ScenarioAssetRequest] = Field(default_factory=list, max_length=100)
    review_priorities: list[str] = Field(default_factory=list, max_length=30)
    constraints: list[str] = Field(default_factory=list, max_length=30)
    instructor_notes: str = Field(default="", max_length=2_000)


class ScenarioDraft(StrictModel):
    schema_version: str = "0.1.0"
    draft_id: str
    revision: int
    status: DraftStatus
    source: str = "mock_ai_suggestion"
    authority: str = "instructor"
    editable_fields: list[str] = Field(default_factory=lambda: ["*"])
    original_prompt: str
    content: ScenarioDraftContent
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None = None
    approved_by: str | None = None
    rejection_reason: str | None = None
    boundary: str = (
        "Mock AI suggestion only. The instructor may change every scenario field and must "
        "explicitly approve the current revision before later publication."
    )


class ScenarioDraftUpdate(StrictModel):
    expected_revision: int = Field(ge=1)
    edited_by: str = Field(min_length=1, max_length=100)
    content: ScenarioDraftContent


class ScenarioDraftApproval(StrictModel):
    expected_revision: int = Field(ge=1)
    approved_by: str = Field(min_length=1, max_length=100)


class ScenarioDraftRejection(StrictModel):
    expected_revision: int = Field(ge=1)
    rejected_by: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=3, max_length=1_000)


class GenerationJob(StrictModel):
    schema_version: str = "0.1.0"
    job_id: str
    status: GenerationJobStatus
    provider: str = "local_mock"
    model_label: str = "no-model-local-fixture"
    requested_by: str
    created_at: datetime
    completed_at: datetime
    draft: ScenarioDraft
    stages: list[str] = Field(
        default_factory=lambda: [
            "request_received",
            "mock_suggestion_created",
            "contract_checked",
            "ready_for_instructor_review",
        ]
    )
    note: str = (
        "No model or external API was called. This job exists to test the instructor workflow."
    )
