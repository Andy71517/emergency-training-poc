# Local Session Logs

The backend writes one JSON object per line (`.jsonl`) under `logs/sessions/` so attempted events, validation findings, and resulting states can be reviewed and replayed in order.

Session logs may contain sensitive training observations in later experiments. They should remain local, are ignored by default, and generally must not be committed. `.gitkeep` exists only to retain this directory.
