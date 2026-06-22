"""Print a concise post-scenario review from a local JSONL log."""

import argparse
import json
from pathlib import Path

from backend.app.logging.review_summary import generate_review_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    summary = generate_review_summary(parser.parse_args().log)
    print(json.dumps(summary, indent=2, sort_keys=True))
