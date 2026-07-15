# Dr. Cameron meeting demo runbook

This is the live screen-share guide.

Use this when the goal is to explain the project clearly in a meeting, not to walk through every file in the repo.

## Meeting goal

By the end of the meeting, Dr. Melissa Cameron and the room should understand:

- where the project started
- why the first POC is intentionally smaller
- what I built so far
- why I built the backend first
- how the work is being staged for a solo developer
- what the demo proves
- what it does not prove yet
- what I want feedback on next

The main message:

> The full project is huge, so I am turning it into checkpoints. The current POC proves that the backend can track trainee actions, update scenario state, flag issues, log the session, and explain what happened afterward.

## What to have open

Before the meeting, open:

- `docs/presentations/emergency-training-poc-overview.pdf`
- a terminal at the repo root
- the local Scenario Review Console at `http://127.0.0.1:8765`
- `docs/presentations/web-demo-phone-speaker-notes.md` on your phone
- `docs/presentations/project-overview-speaker-notes.md`
- `docs/presentations/project-overview-read-through-script.md`
- Unreal, only if the debug panel is ready enough to show

Optional tabs:

- `docs/presentations/project-overview-one-page-handout.md`
- `docs/reports/emergency-training-poc-report.pdf`
- `docs/roadmap.md`
- `docs/ux/dr-cameron-review-rubric.md`

Do not start by showing the whole repo tree. It is too much at once.

## Presentation flow

Use about 7 minutes if the room needs the full origin story.

Use 5 minutes if the room already knows the project background.

### 1. Start with the original vision

Say:

> The full project is an adaptive emergency-response training simulator. It can eventually include Unreal, AI, sensors, assets, physics, validation, and deployment. That is a large project, so I am treating it as the north star.

Show slides 1-2.

### 2. Explain the first narrowing move

Say:

> Before the project becomes immersive, I need the system to keep the truth straight: what action happened, what state changed, what was flagged, and what an instructor can review.

Show slides 3-4.

### 3. Explain how the repo evolved

Say:

> Sprint 0 was scaffolding. The first backend slice made the loop executable. Then replay and review became the strongest proof point.

Show slides 5-9.

### 4. Explain the current architecture

Say:

> The backend owns scenario truth. Unreal is starting as a display client. Assets, physics, AI, and sensing stay future work until the foundation has a clear job for them.

Show slides 10-13.

### 5. Move into the demo and ask for feedback

Say:

> The demo is meant to show the backend loop and review output. The feedback I need is about review usefulness, scenario clarity, and whether the next checkpoints are the right ones.

Show slides 14-15.

## Demo flow

From the repo root, run the local web demo:

```powershell
python scripts/run_web_demo.py
```

Then open `http://127.0.0.1:8765`. Keep `python scripts/run_menu_demo.py` available as a terminal fallback.

Point out:

1. the green backend-online badge
2. one expected path
3. its plain-English review
4. one review-focused path
5. the blocked, resolved, and retried action story
6. environmental cues and discussion points

Use this line during the review output:

> This is the part I care about most: the system can explain what happened, why an action was held, and what changed before a retry—not just say the scenario ended.

## Optional Unreal display moment

Only show Unreal if it is calm and working.

Current safe version:

- show the debug panel
- explain that the text came from backend-shaped display data
- explain that the next step is reading the generated `.txt` file automatically

Do not frame it as a full Unreal client yet.

Good line:

> This is intentionally boring. It proves Unreal can display backend-owned state before I build a scene around it.

## If something breaks

If the backend demo fails:

1. Do not panic.
2. Show `docs/presentations/project-overview-slides.md`.
3. Show `unreal/EmergencyTrainingClient/Data/hallway_debug_panel.sample.txt`.
4. Explain the expected flow from the runbook.
5. Offer to send the latest demo log after the meeting.

Good recovery line:

> The live command is being annoying, but the important structure is still here: event in, backend state update, validation, log, replay, and review.

If Unreal fails:

Say:

> I am not relying on Unreal as the proof point yet. The backend/review loop is the core proof. Unreal is the next display layer.

Then move on.

## Questions to ask Dr. Cameron

Ask these near the end:

1. Does the review summary show the right kind of instructor-facing information?
2. Are the environmental cues clear enough for a first POC?
3. Does the solo-developer checkpoint plan feel realistic?
4. Should the next scenario focus more on fire/EMT decisions, navigation, communication, or scene safety?
5. What would make this more useful as an on-campus research/project demo?

## What not to get pulled into yet

If these come up, acknowledge them as future work:

- real clinical/protocol validation
- real AI scenario adaptation
- full Unreal scene building
- generated assets
- physics simulation
- sensing and pose tracking
- projection mapping
- hub-and-spoke deployment
- cloud production security

Suggested answer:

> That is part of the larger vision, but I am keeping it out of this slice so the foundation stays testable.

## Clean closing

End with:

> The current repo proves the first trusted loop. The next step is making that loop visible in Unreal without moving scenario truth out of the backend.

Then ask for feedback.
