"""Preview the future Unreal text-only debug panel from a JSONL session log."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.unreal_display_preview import display_state_from_log, render_debug_panel  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--json", action="store_true", help="Print the simplified display state as JSON.")
    arguments = parser.parse_args()

    display_state = display_state_from_log(arguments.log)
    if arguments.json:
        print(json.dumps(display_state, indent=2, sort_keys=True))
    else:
        print(render_debug_panel(display_state))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
