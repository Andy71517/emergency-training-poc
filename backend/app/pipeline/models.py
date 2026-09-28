"""Versioned records for the first real generation-to-physics pipeline.

These models deliberately represent records and approval gates only. They do
not submit an ARC job, invoke a model, run Blender, or control Unreal.
"""

import re
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PIPELINE_CONTRACT_VERSION = "0.1.0"
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
SAFE_RECORD_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{2,79}$")


class StrictPipelineModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class GenerationJobStatus(StrEnum):
    REQUESTED = "requested"
    QUEUED = "queued"
    RUNNING = "running"
    CHECKING = "checking"
    FAILED = "failed"
    REVIEW_READY = "review_ready"


class AssetReviewDecision(StrEnum):
    CANDIDATE = "candidate"
    NEEDS_CHANGES = "needs_changes"
    REVIEWED_VISUAL_ONLY = "reviewed_visual_only"
    REVIEWED_COLLISION_CANDIDATE = "reviewed_collision_candidate"
    REJECTED = "rejected"


class ScenarioPublicationStatus(StrEnum):
    SUGGESTED = "suggested"
    INSTRUCTOR_EDITED = "instructor_edited"
    APPROVED = "approved"
    REJECTED = "rejected"


class ArtifactProvenance(StrictPipelineModel):
    source_job_id: str
    model_label: str = Field(min_length=1, max_length=160)
    model_version: str = Field(min_length=1, max_length=160)
    seed: str = Field(min_length=1, max_length=160)
    prompt_digest_sha256: str
    environment_digest: str = Field(min_length=1, max_length=300)

    @field_validator("source_job_id")
    @classmethod
    def safe_source_job_id(cls, value: str) -> str:
        return _safe_record_id(value, "source_job_id")

    @field_validator("prompt_digest_sha256")
    @classmethod
    def valid_prompt_digest(cls, value: str) -> str:
        return _sha256(value, "prompt_digest_sha256")


class ArcGenerationJob(StrictPipelineModel):
    contract_version: str = PIPELINE_CONTRACT_VERSION
    job_id: str
    request_id: str
    status: GenerationJobStatus
    requested_by: str = Field(min_length=1, max_length=100)
    requested_at: datetime
    slurm_job_id: str | None = Field(default=None, min_length=1, max_length=80)
    project_storage_path: str = Field(min_length=1, max_length=500)
    environment_digest: str = Field(min_length=1, max_length=300)
    model_label: str = Field(min_length=1, max_length=160)
    model_version: str = Field(min_length=1, max_length=160)
    seed: str = Field(min_length=1, max_length=160)
    queued_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_summary: str | None = Field(default=None, max_length=1_000)

    @field_validator("job_id", "request_id")
    @classmethod
    def safe_ids(cls, value: str) -> str:
        return _safe_record_id(value, "record_id")

    @model_validator(mode="after")
    def lifecycle_is_consistent(self) -> "ArcGenerationJob":
        if self.status is GenerationJobStatus.FAILED and not self.error_summary:
            raise ValueError("A failed ARC job requires error_summary")
        if self.status is GenerationJobStatus.REVIEW_READY and self.completed_at is None:
            raise ValueError("A review-ready ARC job requires completed_at")
        if self.started_at and self.queued_at and self.started_at < self.queued_at:
            raise ValueError("started_at must not be earlier than queued_at")
        if self.completed_at and self.started_at and self.completed_at < self.started_at:
            raise ValueError("completed_at must not be earlier than started_at")
        return self


class AssetArtifactFile(StrictPipelineModel):
    relative_path: str = Field(min_length=1, max_length=300)
    sha256: str
    media_type: str = Field(min_length=1, max_length=120)

    @field_validator("sha256")
    @classmethod
    def valid_file_digest(cls, value: str) -> str:
        return _sha256(value, "sha256")

    @field_validator("relative_path")
    @classmethod
    def safe_relative_path(cls, value: str) -> str:
        if value.startswith(("/", "\\")) or ".." in value.replace("\\", "/").split("/"):
            raise ValueError("relative_path must stay within its artifact directory")
        return value


class AssetArtifactManifest(StrictPipelineModel):
    contract_version: str = PIPELINE_CONTRACT_VERSION
    asset_id: str
    display_name: str = Field(min_length=1, max_length=160)
    intended_role: str = Field(min_length=1, max_length=500)
    provenance: ArtifactProvenance
    candidate_files: list[AssetArtifactFile] = Field(min_length=1, max_length=100)
    dimensions_m: tuple[float, float, float]
    created_at: datetime

    @field_validator("asset_id")
    @classmethod
    def safe_asset_id(cls, value: str) -> str:
        return _safe_record_id(value, "asset_id")

    @field_validator("dimensions_m")
    @classmethod
    def positive_dimensions(cls, value: tuple[float, float, float]) -> tuple[float, float, float]:
        if any(dimension <= 0 for dimension in value):
            raise ValueError("dimensions_m values must be greater than zero")
        return value


class BlenderAssetReview(StrictPipelineModel):
    contract_version: str = PIPELINE_CONTRACT_VERSION
    asset_id: str
    reviewed_source_sha256: str
    reviewer: str = Field(min_length=1, max_length=100)
    reviewed_at: datetime
    checklist_version: str = Field(min_length=1, max_length=80)
    decision: AssetReviewDecision
    scale_checked: bool
    topology_checked: bool
    materials_checked: bool
    collision_checked: bool
    cleanup_notes: str = Field(default="", max_length=2_000)
    export_file: AssetArtifactFile | None = None

    @field_validator("asset_id")
    @classmethod
    def safe_asset_id(cls, value: str) -> str:
        return _safe_record_id(value, "asset_id")

    @field_validator("reviewed_source_sha256")
    @classmethod
    def valid_source_digest(cls, value: str) -> str:
        return _sha256(value, "reviewed_source_sha256")

    @model_validator(mode="after")
    def approval_has_required_review_evidence(self) -> "BlenderAssetReview":
        if self.decision is AssetReviewDecision.REVIEWED_COLLISION_CANDIDATE:
            if not all(
                [self.scale_checked, self.topology_checked, self.materials_checked, self.collision_checked]
            ):
                raise ValueError("A collision candidate requires all Blender checks")
            if self.export_file is None:
                raise ValueError("A collision candidate requires an export_file")
        return self


class ApprovedAssetPackage(StrictPipelineModel):
    contract_version: str = PIPELINE_CONTRACT_VERSION
    manifest: AssetArtifactManifest
    blender_review: BlenderAssetReview
    approved_by: str = Field(min_length=1, max_length=100)
    approved_at: datetime

    @model_validator(mode="after")
    def only_approved_reviewed_asset_may_be_packaged(self) -> "ApprovedAssetPackage":
        if self.manifest.asset_id != self.blender_review.asset_id:
            raise ValueError("Asset manifest and Blender review must identify the same asset")
        if self.blender_review.decision is not AssetReviewDecision.REVIEWED_COLLISION_CANDIDATE:
            raise ValueError("Only reviewed collision candidates may enter an approved asset package")
        candidate_hashes = {artifact.sha256 for artifact in self.manifest.candidate_files}
        if self.blender_review.reviewed_source_sha256 not in candidate_hashes:
            raise ValueError("Blender review source hash must be listed in the asset manifest")
        return self


class PublishedScenarioPackage(StrictPipelineModel):
    contract_version: str = PIPELINE_CONTRACT_VERSION
    scenario_id: str
    source_job_id: str
    source_job_status: GenerationJobStatus
    draft_revision: int = Field(ge=1)
    draft_status: ScenarioPublicationStatus
    approved_by: str | None = Field(default=None, min_length=1, max_length=100)
    approved_at: datetime | None = None
    package_sha256: str

    @field_validator("scenario_id", "source_job_id")
    @classmethod
    def safe_ids(cls, value: str) -> str:
        return _safe_record_id(value, "record_id")

    @field_validator("package_sha256")
    @classmethod
    def valid_package_digest(cls, value: str) -> str:
        return _sha256(value, "package_sha256")

    @model_validator(mode="after")
    def publication_requires_ready_job_and_instructor_approval(self) -> "PublishedScenarioPackage":
        if self.source_job_status is not GenerationJobStatus.REVIEW_READY:
            raise ValueError("Only a review-ready ARC job may supply a published scenario")
        if self.draft_status is not ScenarioPublicationStatus.APPROVED:
            raise ValueError("Only an instructor-approved draft may be published")
        if self.approved_by is None or self.approved_at is None:
            raise ValueError("Published scenarios require approval evidence")
        return self


def _safe_record_id(value: str, field_name: str) -> str:
    if not SAFE_RECORD_ID_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase safe record identifier")
    return value


def _sha256(value: str, field_name: str) -> str:
    if not SHA256_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return value
