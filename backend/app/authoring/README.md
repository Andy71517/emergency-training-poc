# Scenario Authoring

This module models the first instructor-controlled scenario-generation workflow.

It currently uses a local fixture. No AI model, external API, CS Launch service, or ARC job is connected.

## Authority rule

The AI role is suggestion only. The instructor can replace every field in `ScenarioDraftContent`, including:

- title, summary, environment, difficulty, and duration
- training goals and occupants
- environmental cues and trainee action options
- state-transition suggestions and end conditions
- requested assets and their intended physics role
- review priorities, constraints, and instructor notes

The wildcard value in `editable_fields` makes that boundary explicit in the response contract.

Approval applies only to the current revision. Saving an instructor edit increases the revision number and removes any earlier approval. This prevents an older approval from silently carrying over to changed content.

Approval in this module means the instructor accepted a draft for a later POC stage. It does not mean the content is clinically validated, operationally authoritative, or ready for real responder training.

## Local endpoints

- `POST /api/authoring/jobs` creates a clearly labeled mock suggestion.
- `GET /api/authoring/drafts/{draft_id}` reads the current draft.
- `PUT /api/authoring/drafts/{draft_id}` replaces the full editable content and creates a new revision.
- `POST /api/authoring/drafts/{draft_id}/approve` approves the named current revision.
- `POST /api/authoring/drafts/{draft_id}/reject` rejects the named current revision with a reason.

Drafts and jobs are in memory. Restarting FastAPI clears them. Persistence, accounts, roles, ARC submission, and actual scenario publication remain future work.
