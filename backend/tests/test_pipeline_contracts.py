from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from backend.app.pipeline.models import (
    ApprovedAssetPackage,
    ArcGenerationJob,
    ArtifactProvenance,
    AssetArtifactFile,
    AssetArtifactManifest,
    AssetReviewDecision,
    BlenderAssetReview,
    GenerationJobStatus,
    PublishedScenarioPackage,
    ScenarioPublicationStatus,
)

SHA = "a" * 64
NOW = datetime(2026, 8, 31, tzinfo=UTC)


def _manifest() -> AssetArtifactManifest:
    return AssetArtifactManifest(
        asset_id="leather-chair-candidate-001",
        display_name="Leather chair candidate",
        intended_role="Bounded Unreal movement and contact proof object.",
        provenance=ArtifactProvenance(
            source_job_id="arc-asset-job-001",
            model_label="asset-model",
            model_version="1.0",
            seed="42",
            prompt_digest_sha256=SHA,
            environment_digest="sha256:container-digest",
        ),
        candidate_files=[
            AssetArtifactFile(
                relative_path="candidate/chair.glb", sha256=SHA, media_type="model/gltf-binary"
            )
        ],
        dimensions_m=(0.8, 0.9, 0.85),
        created_at=NOW,
    )


def test_review_ready_arc_job_requires_completion_evidence() -> None:
    with pytest.raises(ValidationError, match="completed_at"):
        ArcGenerationJob(
            job_id="arc-scenario-job-001",
            request_id="scenario-request-001",
            status=GenerationJobStatus.REVIEW_READY,
            requested_by="instructor",
            requested_at=NOW,
            project_storage_path="/projects/example/pipeline",
            environment_digest="sha256:container-digest",
            model_label="scenario-model",
            model_version="1.0",
            seed="42",
        )


def test_asset_manifest_requires_provenance() -> None:
    manifest = _manifest().model_dump()
    manifest.pop("provenance")

    with pytest.raises(ValidationError, match="provenance"):
        AssetArtifactManifest.model_validate(manifest)


def test_collision_candidate_requires_completed_blender_checks_and_export() -> None:
    with pytest.raises(ValidationError, match="all Blender checks"):
        BlenderAssetReview(
            asset_id="leather-chair-candidate-001",
            reviewed_source_sha256=SHA,
            reviewer="reviewer",
            reviewed_at=NOW,
            checklist_version="0.1.0",
            decision=AssetReviewDecision.REVIEWED_COLLISION_CANDIDATE,
            scale_checked=True,
            topology_checked=True,
            materials_checked=True,
            collision_checked=False,
        )


def test_approved_asset_package_rejects_unreviewed_or_mismatched_asset() -> None:
    review = BlenderAssetReview(
        asset_id="different-chair-001",
        reviewed_source_sha256=SHA,
        reviewer="reviewer",
        reviewed_at=NOW,
        checklist_version="0.1.0",
        decision=AssetReviewDecision.REVIEWED_COLLISION_CANDIDATE,
        scale_checked=True,
        topology_checked=True,
        materials_checked=True,
        collision_checked=True,
        export_file=AssetArtifactFile(
            relative_path="export/chair.fbx", sha256="b" * 64, media_type="model/fbx"
        ),
    )

    with pytest.raises(ValidationError, match="same asset"):
        ApprovedAssetPackage(
            manifest=_manifest(), blender_review=review, approved_by="reviewer", approved_at=NOW
        )


def test_published_scenario_requires_ready_job_and_explicit_approval() -> None:
    with pytest.raises(ValidationError, match="instructor-approved"):
        PublishedScenarioPackage(
            scenario_id="generated-smoke-room-001",
            source_job_id="arc-scenario-job-001",
            source_job_status=GenerationJobStatus.REVIEW_READY,
            draft_revision=2,
            draft_status=ScenarioPublicationStatus.INSTRUCTOR_EDITED,
            package_sha256=SHA,
        )


def test_published_scenario_accepts_review_ready_approved_record() -> None:
    package = PublishedScenarioPackage(
        scenario_id="generated-smoke-room-001",
        source_job_id="arc-scenario-job-001",
        source_job_status=GenerationJobStatus.REVIEW_READY,
        draft_revision=2,
        draft_status=ScenarioPublicationStatus.APPROVED,
        approved_by="instructor",
        approved_at=NOW,
        package_sha256=SHA,
    )

    assert package.draft_status is ScenarioPublicationStatus.APPROVED
