# Local Scripts

These scripts are small local helpers for running and checking the POC.

- `run_local_demo.py`: runs the full local demo, including backend startup, sessions, replay, review summaries, and the wooden-chair physics preview.
- `run_backend.sh`: starts the local backend.
- `run_fake_trainee.py`: runs a happy-path session and a warning/error session.
- `run_unreal_contract_harness.py`: tests the future Unreal WebSocket contract without rendering or gameplay.
- `replay_session.py LOG`: replays logged actions and checks the recorded state snapshots.
- `summarize_log.py LOG`: prints a short JSON review summary.

Start with `run_local_demo.py` when you want to show the whole loop. Use the other scripts when you want to inspect one piece at a time.

Keep scripts local and boring. They should not call real AI services, generate assets, run real physics, or make clinical, operational, or training-authority claims.
