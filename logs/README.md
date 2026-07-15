# Local Session Logs

The backend writes session logs as JSONL: one JSON object per line.

Logs live under `logs/sessions/`. They include attempted actions, validation results, and state snapshots in order, so a session can be replayed or summarized later.

Keep `logs/sessions/` small: retain one current happy and warning run for each toy scenario, and remove routine duplicates after testing. The menu only lists this current folder.

Selected milestone logs may be moved into local folders under `logs/archive/`. Archived logs document POC progress, but older snapshots may not strictly replay against today's scenario definitions. Use their saved summaries for historical review. Use Git—not session logs—to restore older code or scenario behavior.

Future logs may contain sensitive training observations. Keep current and archived logs local. They are ignored by Git by default and generally should not be committed.

`.gitkeep` only exists so the folder is present in the repo.
