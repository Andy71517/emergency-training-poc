# Demo Script

Use this flow to show the POC without overselling it.

## One-command local demo

```powershell
python scripts/run_local_demo.py
```

The script:

1. Checks whether the backend is healthy.
2. Starts a local backend if needed.
3. Runs a happy-path session.
4. Runs a warning/error session.
5. Writes JSONL logs for both sessions.
6. Replays each log to prove deterministic behavior.
7. Prints a sectioned review summary for each session.
8. Shows the wooden-chair environment preview with physics disabled and enabled.
9. Shows whether the room was scanned, the chair was moved, the entry door was checked/opened, communication was recorded, smoke/visibility was checked, the environment was monitored, and the occupant was located.

The happy path records the room scan, checks the door, moves the wooden chair, opens the entry door, communicates status, checks smoke/visibility, monitors the environment, enters the room, locates the occupant, and then records the removal step.

The warning/error path intentionally skips some cues. The backend then explains those skipped steps in the review instead of pretending the run was clean.

The door's open/closed state and the smoke/visibility cue's checked/unchecked state matter in the scenario. Door type, lock state, collision shape, mass, hinge side, swing direction, force directions, and real smoke behavior are metadata only for now.

The physics preview is only metadata. It does not generate a mesh, load an Unreal scene, run gravity, run collision, apply force, or simulate movement.

Keep the disclaimer visible in any demo: this is illustrative POC behavior, not clinical or operational guidance.

The review summary is the main proof point for Dr. Cameron: it should show that the system can explain what happened, what cues were noticed or missed, and why the backend flagged the run.

After the demo, use `docs/ux/dr-cameron-review-rubric.md` to discuss what the POC proves, what is still rough, and what has been intentionally avoided for now.
