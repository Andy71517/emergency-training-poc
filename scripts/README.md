# Local Scripts

These scripts are small local helpers for running and checking the POC.

- `run_local_demo.py`: runs the full local demo, including backend startup, sessions, replay, review summaries, and the wooden-chair physics preview.
- `run_backend.sh`: starts the local backend.
- `run_fake_trainee.py`: runs a happy-path session and a warning/error session.
- `run_unreal_contract_harness.py`: tests the future Unreal WebSocket contract without rendering or gameplay.
- `preview_unreal_display.py LOG`: prints the future Unreal text-only debug display from a session log. Add `--json` to print the simplified display-state contract.
- `preview_unreal_display.py --display-state PATH`: previews a checked-in Unreal display-state sample JSON before building it in Unreal.
- `replay_session.py LOG`: replays logged actions and checks the recorded state snapshots.
- `summarize_log.py LOG`: prints a short JSON review summary.
- `build_doc_pdfs.py`: builds the small PDF submission packet under `docs/submission-packet/`.

Start with `run_local_demo.py` when you want to show the whole loop. Use the other scripts when you want to inspect one piece at a time.

When a packet-facing Markdown doc changes, run:

```powershell
python scripts/build_doc_pdfs.py
```

That keeps the official four-PDF packet in sync with the editable docs. Folder READMEs stay as GitHub docs and do not need PDF copies.

Keep scripts local and boring. They should not call real AI services, generate assets, run real physics, or make clinical, operational, or training-authority claims.
