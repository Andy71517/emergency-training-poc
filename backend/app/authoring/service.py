"""In-memory mock authoring service for the funding-proof workflow."""

from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4

from backend.app.authoring.models import (
    DraftStatus,
    GenerationJob,
    ScenarioActionOption,
    ScenarioAssetRequest,
    ScenarioCue,
    ScenarioDraft,
    ScenarioDraftApproval,
    ScenarioDraftContent,
    ScenarioDraftRejection,
    ScenarioDraftUpdate,
    ScenarioGenerationRequest,
    ScenarioTransitionDraft,
)


class DraftNotFoundError(KeyError):
    """Raised when a requested draft does not exist."""


class DraftRevisionConflictError(ValueError):
    """Raised when an instructor edits an older draft revision."""


class ScenarioAuthoringService:
    def __init__(self) -> None:
        self._drafts: dict[str, ScenarioDraft] = {}
        self._jobs: dict[str, GenerationJob] = {}
        self._lock = Lock()

    def create_mock_job(self, request: ScenarioGenerationRequest) -> GenerationJob:
        now = datetime.now(UTC)
        draft_id = f"draft-{uuid4().hex}"
        draft = ScenarioDraft(
            draft_id=draft_id,
            revision=1,
            status=DraftStatus.SUGGESTED,
            original_prompt=request.prompt,
            content=_smoke_room_suggestion(request.prompt),
            created_at=now,
            updated_at=now,
        )
        job = GenerationJob(
            job_id=f"job-{uuid4().hex}",
            status="review_ready",
            requested_by=request.requested_by,
            created_at=now,
            completed_at=now,
            draft=draft,
        )
        with self._lock:
            self._drafts[draft_id] = draft
            self._jobs[job.job_id] = job
        return job.model_copy(deep=True)

    def get_draft(self, draft_id: str) -> ScenarioDraft:
        with self._lock:
            draft = self._drafts.get(draft_id)
            if draft is None:
                raise DraftNotFoundError(draft_id)
            return draft.model_copy(deep=True)

    def update_draft(self, draft_id: str, update: ScenarioDraftUpdate) -> ScenarioDraft:
        with self._lock:
            current = self._get_locked(draft_id)
            self._ensure_revision(current, update.expected_revision)
            updated = current.model_copy(
                update={
                    "revision": current.revision + 1,
                    "status": DraftStatus.INSTRUCTOR_EDITED,
                    "content": update.content,
                    "updated_at": datetime.now(UTC),
                    "approved_at": None,
                    "approved_by": None,
                    "rejection_reason": None,
                },
                deep=True,
            )
            self._drafts[draft_id] = updated
            return updated.model_copy(deep=True)

    def approve_draft(self, draft_id: str, approval: ScenarioDraftApproval) -> ScenarioDraft:
        with self._lock:
            current = self._get_locked(draft_id)
            self._ensure_revision(current, approval.expected_revision)
            now = datetime.now(UTC)
            approved = current.model_copy(
                update={
                    "status": DraftStatus.APPROVED,
                    "approved_at": now,
                    "approved_by": approval.approved_by,
                    "updated_at": now,
                    "rejection_reason": None,
                },
                deep=True,
            )
            self._drafts[draft_id] = approved
            return approved.model_copy(deep=True)

    def reject_draft(self, draft_id: str, rejection: ScenarioDraftRejection) -> ScenarioDraft:
        with self._lock:
            current = self._get_locked(draft_id)
            self._ensure_revision(current, rejection.expected_revision)
            rejected = current.model_copy(
                update={
                    "status": DraftStatus.REJECTED,
                    "updated_at": datetime.now(UTC),
                    "approved_at": None,
                    "approved_by": None,
                    "rejection_reason": rejection.reason,
                },
                deep=True,
            )
            self._drafts[draft_id] = rejected
            return rejected.model_copy(deep=True)

    def _get_locked(self, draft_id: str) -> ScenarioDraft:
        draft = self._drafts.get(draft_id)
        if draft is None:
            raise DraftNotFoundError(draft_id)
        return draft

    @staticmethod
    def _ensure_revision(draft: ScenarioDraft, expected_revision: int) -> None:
        if draft.revision != expected_revision:
            raise DraftRevisionConflictError(
                f"Draft revision changed. Expected {expected_revision}, current is {draft.revision}."
            )


def _smoke_room_suggestion(prompt: str) -> ScenarioDraftContent:
    return ScenarioDraftContent(
        title="Suggested immersive smoke-room scenario",
        summary=(
            "A draft room-based scenario for testing instructor authoring, environmental cues, "
            "an interactive obstacle, and an explainable review trail."
        ),
        training_goals=[
            "Notice and discuss visible environmental cues",
            "Explain decisions as the room state changes",
            "Review the action sequence with an instructor",
        ],
        environment=(
            "A small visualization room with reduced-visibility presentation cues, an entry "
            "door, an occupant placeholder, and a leather chair near the travel path."
        ),
        difficulty="Instructor controlled",
        estimated_duration_minutes=8,
        occupants=["One non-clinical occupant placeholder"],
        cues=[
            ScenarioCue(
                cue_id="entry_visibility",
                label="Entry visibility",
                description="A visual cue suggests reduced visibility near the doorway.",
            ),
            ScenarioCue(
                cue_id="chair_position",
                label="Leather chair position",
                description="A chair is placed near the intended path for observation and interaction.",
            ),
        ],
        actions=[
            ScenarioActionOption(
                action_id="observe_room",
                label="Observe the room",
                intended_effect="Record which environmental cues the trainee noticed.",
            ),
            ScenarioActionOption(
                action_id="interact_with_chair",
                label="Interact with the chair",
                intended_effect="Send an interaction to Unreal and record the resulting state change.",
            ),
            ScenarioActionOption(
                action_id="request_review",
                label="Finish and review",
                intended_effect="End the draft exercise and open the instructor review.",
            ),
        ],
        transitions=[
            ScenarioTransitionDraft(
                transition_id="record-observation",
                when="The trainee chooses to observe the room.",
                then="The backend records the selected cues as noticed.",
            ),
            ScenarioTransitionDraft(
                transition_id="record-chair-interaction",
                when="The trainee interacts with the generated chair in Unreal.",
                then="Unreal reports the interaction and the backend records the approved state event.",
            ),
        ],
        end_conditions=["The instructor or trainee explicitly finishes the exercise"],
        assets=[
            ScenarioAssetRequest(
                asset_id="leather_chair_candidate",
                label="Leather chair",
                purpose="Visible room object and bounded physics-pipeline test candidate.",
                physics_intent=(
                    "After human asset review, Unreal may configure collision, mass, friction, "
                    "gravity, and forces. The generation model does not provide physics authority."
                ),
            )
        ],
        review_priorities=[
            "What the trainee noticed",
            "What changed after interaction",
            "Which parts need instructor discussion",
        ],
        constraints=[
            "Draft only until instructor approval",
            "No clinical validity or operational guidance claims",
            "Backend remains the source of approved scenario state",
        ],
        instructor_notes=f"Original instructor request: {prompt}",
    )
