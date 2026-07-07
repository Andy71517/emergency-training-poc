# Emergency Training Simulator POC

From full-system idea to a working backend-first proof

Project update for Dr. Melissa Cameron

---

# The starting point was much bigger than this repo

The original goal points toward a full adaptive training platform.

- Unreal-style immersive scenes
- AI-driven scenario changes
- sensing and trainee action interpretation
- validation and instructor review
- physical objects, assets, and deployment later

This POC is the first safe slice of that bigger idea.

---

# The first useful question was smaller

Before building the spectacle, I need the system to keep the truth straight.

- What action happened?
- What state changed?
- What was warned or rejected?
- What can an instructor review afterward?

That is why I started backend-first.

---

# My solo-dev strategy is checkpoints, not chaos

This is a huge ask for one person, so I am turning it into thin slices.

- prove one loop at a time
- keep every slice demoable
- delay expensive tools until they have a job
- keep the backend as the source of truth

Scope control is how the big idea stays buildable.

---

# What Sprint 0 created

The first pass built the project skeleton and boundaries.

- docs, architecture notes, and ADRs
- message schemas and examples
- toy scenarios and validation rules
- backend placeholders, scripts, logs
- Unreal and asset pipeline placeholders

This made the project organized before it became complex.

---

# The first working loop is now real

The backend can run the core POC loop end to end.

```text
trainee action -> backend -> scenario state
-> validation -> client update -> log -> review
```

What exists today:

- FastAPI WebSocket backend
- deterministic YAML scenarios
- JSONL logs, replay, and review summaries

---

# The review summary became the strongest proof

The demo does not just say "it ran."

It explains what happened.

- action timeline
- final state
- warnings and errors
- replay verification
- plain-English reviewer notes

That is the start of instructor-facing value.

---

# The scenarios are small, but no longer flat

The backend now tracks environmental cues.

- smoke and visibility
- wooden chair blocking a path
- door open or closed
- occupant visibility
- hallway obstacle and exit-door state

These are toy rules, not emergency guidance.

---

# A second scenario proved the engine can generalize

The blocked-exit hallway scenario uses the same backend loop with different state.

- different environment
- different objects
- different warnings
- same deterministic engine

This is a step toward a future scenario library.

---

# Unreal is starting as a display client

Unreal should not become the simulator brain.

Current path:

```text
display JSON -> generated debug text -> Unreal panel
```

Next path:

```text
text file -> JSON parsing -> live backend WebSocket
```

---

# Current architecture keeps the truth in one place

Backend owns:

- scenario state
- validation results
- logs and replay
- review summary

Unreal displays state and later sends simple action requests.

Assets, physics, AI, sensing, and deployment stay staged.

---

# Timeline: realistic solo-dev checkpoints

Now:

- backend proof and review loop
- Unreal debug display started

Next:

- Unreal reads text, then JSON, then WebSocket state

Later:

- scene shell, reviewed assets, physics/AI/sensing experiments

---

# What I am not claiming yet

This is still a proof of concept.

- no real AI calls
- no clinical or protocol authority
- no real physics
- no generated assets
- no full Unreal scene
- no production deployment

The boundary is deliberate.

---

# Demo and feedback ask

Demo:

```powershell
python scripts/run_local_demo.py
```

What I want feedback on:

- Is the review useful for instructors?
- Are the environmental cues clear?
- Is the solo-dev roadmap realistic?
- What scenario should come next?

---

# Closing

The project is evolving in the right order.

First prove the loop.

Then make it visible.

Then make it immersive.

One monster at a time.
