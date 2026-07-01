# Local Session Logs

The backend writes session logs as JSONL: one JSON object per line.

Logs live under `logs/sessions/`. They include attempted actions, validation results, and state snapshots in order, so a session can be replayed or summarized later.

Future logs may contain sensitive training observations. Keep them local. They are ignored by Git by default and generally should not be committed.

`.gitkeep` only exists so the folder is present in the repo.
