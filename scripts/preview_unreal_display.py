"""Preview the future Unreal text-only debug panel from a log or display-state JSON."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.unreal_display_preview import display_state_from_log, render_debug_panel


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, nargs="?", help="JSONL session log to convert into display state.")
    parser.add_argument(
        "--display-state",
        type=Path,
        help="Checked-in display-state JSON file to preview directly.",
    )
    parser.add_argument("--json", action="store_true", help="Print the simplified display state as JSON.")
    arguments = parser.parse_args()

    if arguments.display_state is not None:
        display_state = json.loads(arguments.display_state.read_text(encoding="utf-8"))
    elif arguments.log is not None:
        display_state = display_state_from_log(arguments.log)
    else:
        parser.error("provide a JSONL log or --display-state JSON file")

    if arguments.json:
        print(json.dumps(display_state, indent=2, sort_keys=True))
    else:
        print(render_debug_panel(display_state))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
