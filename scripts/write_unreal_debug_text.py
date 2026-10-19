"""Write Unreal-friendly debug text from a display-state JSON file."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.unreal_display_preview import render_debug_panel

DEFAULT_DISPLAY_STATE = (
    REPO_ROOT / "unreal" / "EmergencyTrainingClient" / "Data" / "hallway_display_state.sample.json"
)
DEFAULT_OUTPUT = (
    REPO_ROOT / "unreal" / "EmergencyTrainingClient" / "Data" / "hallway_debug_panel.sample.txt"
)


def load_display_state(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def debug_text_from_display_state(path: Path) -> str:
    return render_debug_panel(load_display_state(path))


def write_debug_text(display_state_path: Path, output_path: Path) -> str:
    debug_text = debug_text_from_display_state(display_state_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(debug_text + "\n", encoding="utf-8")
    return debug_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--display-state",
        type=Path,
        default=DEFAULT_DISPLAY_STATE,
        help="Display-state JSON to turn into simple debug text.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Text file to write for Unreal's first debug panel.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Also print the generated text after writing it.",
    )
    arguments = parser.parse_args()

    debug_text = write_debug_text(arguments.display_state, arguments.output)
    print(f"Wrote Unreal debug text: {arguments.output}")
    if arguments.stdout:
        print()
        print(debug_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
