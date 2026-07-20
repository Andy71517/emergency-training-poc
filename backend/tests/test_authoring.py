from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import create_app


def _create_draft(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/authoring/jobs",
        json={
            "prompt": "Suggest a smoke-room exercise with a leather chair.",
            "requested_by": "test-instructor",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_mock_job_is_clearly_labeled_and_requires_instructor_approval(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    job = _create_draft(client)

    assert job["status"] == "review_ready"
    assert job["provider"] == "local_mock"
    assert job["model_label"] == "no-model-local-fixture"
    assert "No model or external API" in job["note"]
    assert job["draft"]["status"] == "suggested"
    assert job["draft"]["authority"] == "instructor"
    assert job["draft"]["editable_fields"] == ["*"]
    assert job["draft"]["approved_at"] is None


def test_instructor_can_replace_all_scenario_content_before_approval(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    job = _create_draft(client)
    draft = job["draft"]
    content = draft["content"]
    content.update(
        {
            "title": "Instructor-owned room exercise",
            "summary": "The instructor rewrote the entire suggested scenario.",
            "training_goals": ["Instructor-selected discussion goal"],
            "environment": "Instructor-selected room layout",
            "difficulty": "Introductory",
            "estimated_duration_minutes": 12,
            "occupants": [],
            "cues": [],
            "actions": [],
            "transitions": [],
            "end_conditions": ["Instructor ends the exercise"],
            "assets": [],
            "review_priorities": ["Instructor-selected review point"],
            "constraints": ["Instructor-selected constraint"],
            "instructor_notes": "This content replaces the mock suggestion.",
        }
    )

    response = client.put(
        f"/api/authoring/drafts/{draft['draft_id']}",
        json={
            "expected_revision": draft["revision"],
            "edited_by": "test-instructor",
            "content": content,
        },
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["revision"] == 2
    assert updated["status"] == "instructor_edited"
    assert updated["content"]["title"] == "Instructor-owned room exercise"
    assert updated["content"]["assets"] == []


def test_approval_applies_only_to_the_current_revision(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    draft = _create_draft(client)["draft"]
    content = draft["content"]
    content["title"] = "Revision two"
    updated = client.put(
        f"/api/authoring/drafts/{draft['draft_id']}",
        json={
            "expected_revision": 1,
            "edited_by": "test-instructor",
            "content": content,
        },
    ).json()
    stale_approval = client.post(
        f"/api/authoring/drafts/{draft['draft_id']}/approve",
        json={"expected_revision": 1, "approved_by": "test-instructor"},
    )
    current_approval = client.post(
        f"/api/authoring/drafts/{draft['draft_id']}/approve",
        json={"expected_revision": updated["revision"], "approved_by": "test-instructor"},
    )

    assert stale_approval.status_code == 409
    assert current_approval.status_code == 200
    assert current_approval.json()["status"] == "approved"
    assert current_approval.json()["approved_by"] == "test-instructor"


def test_editing_an_approved_draft_removes_approval(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    draft = _create_draft(client)["draft"]
    approved = client.post(
        f"/api/authoring/drafts/{draft['draft_id']}/approve",
        json={"expected_revision": 1, "approved_by": "test-instructor"},
    ).json()
    content = approved["content"]
    content["title"] = "Edited after approval"

    response = client.put(
        f"/api/authoring/drafts/{draft['draft_id']}",
        json={
            "expected_revision": approved["revision"],
            "edited_by": "test-instructor",
            "content": content,
        },
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["status"] == "instructor_edited"
    assert updated["approved_at"] is None
    assert updated["approved_by"] is None


def test_instructor_can_reject_a_suggestion_with_a_reason(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    draft = _create_draft(client)["draft"]

    response = client.post(
        f"/api/authoring/drafts/{draft['draft_id']}/reject",
        json={
            "expected_revision": draft["revision"],
            "rejected_by": "test-instructor",
            "reason": "The room goals need a different focus.",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert response.json()["rejection_reason"] == "The room goals need a different focus."
