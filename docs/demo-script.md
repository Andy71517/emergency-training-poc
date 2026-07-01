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
7. Prints a short review summary for each session.
8. Shows the wooden-chair environment preview with physics disabled and enabled.

The physics preview is only metadata. It does not generate a mesh, load an Unreal scene, run collision, or simulate movement.

Keep the disclaimer visible in any demo: this is illustrative POC behavior, not clinical or operational guidance.
