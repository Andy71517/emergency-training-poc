# Local Scripts

These scripts are small local helpers for running and checking the POC.

- `run_local_demo.py`: runs the full local demo, including backend startup, sessions, replay, review summaries, and the wooden-chair physics preview.
- `run_menu_demo.py`: presentation-friendly menu for the two toy scenarios. It can run happy and warning paths, replay or summarize saved logs, compare two reviews, check backend status, list scenarios, and accept a small custom action sequence.
- `run_backend.sh`: starts the local backend.
- `run_fake_trainee.py`: runs a happy-path session and a warning/error session.
- `run_unreal_contract_harness.py`: tests the future Unreal WebSocket contract without rendering or gameplay.
- `preview_unreal_display.py LOG`: prints the future Unreal text-only debug display from a session log. Add `--json` to print the simplified display-state contract.
- `preview_unreal_display.py --display-state PATH`: previews a checked-in Unreal display-state sample JSON before building it in Unreal.
- `write_unreal_debug_text.py`: turns a display-state JSON file into a simple `.txt` file that Unreal can show before it parses JSON directly.
- `replay_session.py LOG`: replays logged actions and checks the recorded state snapshots.
- `summarize_log.py LOG`: prints a short JSON review summary.
- `build_doc_pdfs.py`: builds the small PDF submission packet under `docs/submission-packet/`.

Start with `run_local_demo.py` when you want to show the whole loop. Use the other scripts when you want to inspect one piece at a time.

For a guided Dr. Cameron-friendly backend walkthrough, run:

```powershell
python scripts/run_menu_demo.py
```

This is presentation mode. It uses a clearly announced 2.5-second pause, offers optional action details, and asks before starting each additional path when option 5 runs all four.

For the no-delay developer/test mode, run:

```powershell
python scripts/run_menu_demo.py --fast
```

Fast mode shows action details automatically and runs option 5 without between-run prompts. Both modes start the local backend if needed and produce the same deterministic session logs. The helper's warnings, errors, comparisons, and reviews are not clinical validation, real emergency guidance, or protocol authority.

For the first Unreal debug panel, the easiest path is:

```powershell
python scripts/write_unreal_debug_text.py
```

That refreshes:

```text
unreal/EmergencyTrainingClient/Data/hallway_debug_panel.sample.txt
```

Unreal can read that text file before it learns how to parse the full JSON contract.

When a packet-facing Markdown doc changes, run:

```powershell
python scripts/build_doc_pdfs.py
```

That keeps the official four-PDF packet in sync with the editable docs. Folder READMEs stay as GitHub docs and do not need PDF copies.

Keep scripts local and boring. They should not call real AI services, generate assets, run real physics, or make clinical, operational, or training-authority claims.
