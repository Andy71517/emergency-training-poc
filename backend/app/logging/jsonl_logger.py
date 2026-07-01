"""Append-only local JSONL session logging."""

import json
from pathlib import Path
from threading import Lock
from typing import Any

from backend.app.security import ensure_safe_identifier


class JsonlSessionLogger:
    def __init__(self, log_directory: Path) -> None:
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def path_for(self, session_id: str) -> Path:
        safe_id = ensure_safe_identifier(session_id, "session_id")
        return self.log_directory / f"{safe_id}.jsonl"

    def append(self, session_id: str, entry: dict[str, Any]) -> Path:
        path = self.path_for(session_id)
        line = json.dumps(entry, separators=(",", ":"), ensure_ascii=False, default=str)
        with self._lock, path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(line + "\n")
        return path
