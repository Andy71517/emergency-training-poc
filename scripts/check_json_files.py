"""Check that checked-in JSON files parse cleanly.

This is intentionally tiny. It catches broken schema/example JSON in CI without
turning the repo into a full schema validation system yet.
"""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
JSON_ROOTS = [REPO_ROOT / "schemas", REPO_ROOT / "unreal"]


def iter_json_files() -> list[Path]:
    files: list[Path] = []
    for root in JSON_ROOTS:
        if root.exists():
            files.extend(sorted(root.rglob("*.json")))
    return files


def main() -> int:
    files = iter_json_files()
    for path in files:
        json.loads(path.read_text(encoding="utf-8"))
    print(f"Checked {len(files)} JSON files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

