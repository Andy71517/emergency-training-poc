"""Build and serve the local one-page presentation demo from FastAPI."""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WEB_DIRECTORY = REPO_ROOT / "web"
WEB_BUILD_DIRECTORY = WEB_DIRECTORY / "dist"


def npm_command() -> str:
    command = "npm.cmd" if os.name == "nt" else "npm"
    resolved = shutil.which(command)
    if resolved is None:
        raise RuntimeError("npm was not found. Install Node.js before running the webpage demo.")
    return resolved


def build_webpage() -> None:
    print("Preparing the local presentation webpage...")
    subprocess.run([npm_command(), "run", "build"], cwd=WEB_DIRECTORY, check=True)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="Reuse web/dist instead of rebuilding the webpage.",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    if not arguments.no_build or not WEB_BUILD_DIRECTORY.is_dir():
        build_webpage()
    print(f"\nPresentation webpage: http://{arguments.host}:{arguments.port}")
    print("Press Ctrl+C when the local demo is finished.\n")
    try:
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "backend.app.main:app",
                "--host",
                arguments.host,
                "--port",
                str(arguments.port),
            ],
            cwd=REPO_ROOT,
            check=False,
        ).returncode
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
