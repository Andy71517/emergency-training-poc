# Speaker notes

These notes match `project-overview-slides.md`.

The deck is shorter now, so each slide does more work. Keep the slide visible, then use these notes to fill in the context naturally.

Tone: chill but prepared. This is for Dr. Melissa Cameron, who is both the first project audience and my on-campus job supervisor, so the voice should be honest, clear, and respectful without sounding stiff.

## 1. Emergency Training Simulator POC

Open by framing this as a project update, not a final-product pitch.

Suggested line:

> I want to show how this started as a big full-system idea, what I have built so far, and how I am turning it into realistic checkpoints as a solo developer.

Set the main expectation: this is not the finished simulator. It is the first reliable proof layer.

## 2. The starting point was much bigger than this repo

Explain the original ambition.

The full vision points toward an adaptive emergency-response training simulator with immersive environments, AI-assisted scenario changes, sensing, validation, review, physical objects, and deployment later.

Make the solo-dev scale clear:

> That full direction is a research-and-engineering program. The current repo is the first safe slice of it.

## 3. The first useful question was smaller

This slide explains the first narrowing decision.

Before worrying about a full scene, the system needs to keep track of truth: what action happened, what changed, what was flagged, and what an instructor can review.

This is the reason the project started backend-first instead of Unreal-first.

## 4. My solo-dev strategy is checkpoints, not chaos

Frame scope control as judgment, not lack of ambition.

Say that each slice should prove one idea, be demoable, and avoid pulling in expensive tools before they have a clear job.

Suggested line:

> Scope control here is not me shrinking the project. It is how I keep the project buildable.

## 5. What Sprint 0 created

Explain the first repo pass.

Sprint 0 created structure: docs, ADRs, schemas, scenarios, validation rules, backend folders, logs, Unreal placeholders, and asset pipeline notes.

The main value was setting boundaries early:

- backend owns truth
- validation is POC rule checking
- Unreal is a client, not the brain
- assets, physics, AI, and sensing are future stages

## 6. The first working loop is now real

Walk through the loop.

Trainee action enters the backend. Scenario state updates. Validation checks it. The client can receive state. A JSONL log is written. Replay and review can explain the session.

Mention deterministic behavior:

> Same ordered inputs should produce the same outputs, which makes the POC testable and explainable.

## 7. The review summary became the strongest proof

This is the strongest slide for Dr. Cameron.

The review summary turns a run into an explanation. It can show the action timeline, final state, warnings, errors, replay verification, and reviewer notes.

Suggested line:

> The strongest proof is not "the demo ran." It is "the system can explain what happened."

## 8. The scenarios are small, but no longer flat

Explain the scenario richness.

The smoke-room scenario now includes smoke/visibility, a wooden chair, a door, occupant visibility, communication, scanning, and environmental monitoring.

The hallway scenario includes obstacle and exit-door cues.

Be clear:

> These are toy rules for software testing, not real emergency guidance.

## 9. A second scenario proved the engine can generalize

Explain why the second scenario matters.

The hallway scenario uses the same backend engine but different state, objects, and warnings. That proves the backend is not only built around one room.

This is a small step toward a future scenario library.

## 10. Unreal is starting as a display client

Explain the current Unreal direction.

Unreal is being introduced carefully. The first job is showing backend-owned state in a debug panel.

The current bridge is:

```text
display JSON -> generated debug text -> Unreal panel
```

Next, Unreal reads the text file itself. Then it parses JSON. Then it connects to the backend.

## 11. Current architecture keeps the truth in one place

Explain the system split.

Backend owns scenario state, validation, logs, replay, and review.

Unreal displays state and later sends simple action requests.

Assets, physics, AI, sensing, and deployment are staged so they do not make the foundation messy too early.

## 12. Timeline: realistic solo-dev checkpoints

Walk through the timeline without overpromising.

Now:

- backend proof and review loop
- Unreal display started

Next:

- Unreal reads text
- Unreal parses JSON
- Unreal receives live backend WebSocket state

Later:

- simple scene shell
- reviewed assets
- physics, AI, and sensing experiments

## 13. What I am not claiming yet

Use this slide to protect credibility.

Say plainly that the repo does not have real AI calls, clinical validation, protocol authority, real physics, generated assets, a full Unreal scene, or production deployment.

Suggested line:

> The boundary is deliberate. It keeps the POC honest and testable.

## 14. Demo and feedback ask

Transition into the demo.

Run:

```powershell
python scripts/run_local_demo.py
```

Ask for feedback on:

- instructor usefulness of the review
- clarity of environmental cues
- realism of the solo-dev roadmap
- what scenario should come next

## 15. Closing

End with the simple build order.

First prove the loop. Then make it visible. Then make it immersive.

Suggested closer:

> I am trying to build the exciting version eventually, but I am doing it in an order where each layer has something solid underneath it.
