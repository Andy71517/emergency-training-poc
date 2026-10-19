"""Print a concise post-scenario review from a local JSONL log."""

import argparse
import json
from pathlib import Path

from backend.app.logging.review_summary import format_review_summary, generate_review_summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--json", action="store_true", help="Print the structured JSON summary.")
    arguments = parser.parse_args()
    summary = generate_review_summary(arguments.log)
    if arguments.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(format_review_summary(summary, log_path=arguments.log))
