"""Run the full local POC demo: sessions, logs, replay, review, and chair preview."""

import argparse
import asyncio
import json
import subprocess
import sys
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

import websockets

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.adapters.manual_input_adapter import build_action_message  # noqa: E402
from backend.app.logging.review_summary import generate_review_summary  # noqa: E402
from scripts.replay_session import replay  # noqa: E402


DEFAULT_HTTP_URL = "http://127.0.0.1:8765"
DEFAULT_LOG_DIRECTORY = Path("logs") / "sessions"
HAPPY_ACTIONS = [
    "assess_scene",
    "confirm_ppe",
    "request_backup",
    "move_obstacle",
    "open_door",
    "enter_room",
    "remove_occupant",
]
WARNING_ERROR_ACTIONS = [
    "confirm_ppe",
    "enter_room",
    "assess_scene",
    "confirm_ppe",
    "request_backup",
    "move_obstacle",
    "enter_room",
    "stop_scenario",
]
PhysicsPreview = Literal["disabled", "enabled", "both"]


@dataclass(frozen=True)
class DemoSession:
    label: str
    session_id: str
    actions: list[str]
    log_path: Path


def is_backend_healthy(http_url: str, timeout_seconds: float = 1.0) -> bool:
    try:
        with urlopen(f"{http_url.rstrip('/')}/health", timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return response.status == 200 and payload.get("status") == "ok"
    except (OSError, URLError, TimeoutError, json.JSONDecodeError):
        return False


def start_backend(http_url: str) -> subprocess.Popen[bytes]:
    parsed = urlparse(http_url)
    host = parsed.hostname or "127.0.0.1"
    port = str(parsed.port or 8000)
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.app.main:app",
            "--host",
            host,
            "--port",
            port,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def wait_for_backend(http_url: str, timeout_seconds: float = 8.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if is_backend_healthy(http_url, timeout_seconds=0.5):
            return True
        time.sleep(0.25)
    return False


def make_session_id(prefix: str, label: str, run_id: str) -> str:
    safe_prefix = sanitize_id(prefix)
    safe_label = sanitize_id(label)
    safe_run = sanitize_id(run_id)
    return f"{safe_prefix}-{safe_label}-{safe_run}"


def sanitize_id(value: str) -> str:
    safe = "".join(
        character if character.isalnum() or character in "-_" else "-"
        for character in value.lower()
    )
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe.strip("-_") or "demo"


def log_path_for(session_id: str, log_directory: Path = DEFAULT_LOG_DIRECTORY) -> Path:
    return log_directory / f"{session_id}.jsonl"


def ws_url_from_http(http_url: str) -> str:
    parsed = urlparse(http_url)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    netloc = parsed.netloc or "127.0.0.1:8765"
    return f"{scheme}://{netloc}"


def build_demo_sessions(prefix: str, run_id: str) -> list[DemoSession]:
    happy_id = make_session_id(prefix, "happy", run_id)
    warning_id = make_session_id(prefix, "warning-error", run_id)
    return [
        DemoSession("happy path", happy_id, HAPPY_ACTIONS, log_path_for(happy_id)),
        DemoSession("warning/error path", warning_id, WARNING_ERROR_ACTIONS, log_path_for(warning_id)),
    ]


async def run_websocket_session(ws_url: str, session: DemoSession) -> list[dict[str, Any]]:
    uri = f"{ws_url.rstrip('/')}/ws/sessions/{session.session_id}"
    received: list[dict[str, Any]] = []
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"message_type": "start_session"}))
        received.append(json.loads(await websocket.recv()))

        for sequence_number, action_type in enumerate(session.actions, start=1):
            message = build_action_message(
                session_id=session.session_id,
                action_type=action_type,
                sequence_number=sequence_number,
            )
            await websocket.send(message.model_dump_json())
            update = json.loads(await websocket.recv())
            received.append(update)
            if update.get("scenario_state", {}).get("is_terminal"):
                received.append(json.loads(await websocket.recv()))
                break
    return received


def chair_previews(mode: PhysicsPreview) -> list[dict[str, Any]]:
    previews = []
    if mode in {"disabled", "both"}:
        previews.append(
            {
                "object_id": "wooden_chair_poc",
                "label": "Wooden chair",
                "physics_enabled": False,
                "role": "visual/context preview only",
                "notes": [
                    "No mesh is generated or loaded.",
                    "No gravity, collision, mass, tipping, or movement is simulated.",
                ],
            }
        )
    if mode in {"enabled", "both"}:
        previews.append(
            {
                "object_id": "wooden_chair_poc",
                "label": "Wooden chair",
                "physics_enabled": True,
                "role": "future physics candidate preview",
                "notes": [
                    "Intended future checks: collision, tipping, blocked movement, and placement.",
                    "Mass/material values are assumptions to review later, not active simulation.",
                    "Mass alone does not cover gravity; real gravity needs a physics engine later.",
                ],
            }
        )
    return previews


def render_chair_preview(previews: Iterable[dict[str, Any]]) -> str:
    lines = ["Wooden chair environment preview"]
    for preview in previews:
        enabled = "enabled preview" if preview["physics_enabled"] else "disabled"
        lines.append(f"- {preview['label']} ({enabled}): {preview['role']}")
        for note in preview["notes"]:
            lines.append(f"  - {note}")
    return "\n".join(lines)


def render_review_report(
    *,
    session: DemoSession,
    summary: dict[str, Any],
    replay_result: dict[str, Any],
    physics_preview: PhysicsPreview = "both",
) -> str:
    final_state = summary.get("final_state") or {}
    warnings = summary.get("warnings") or []
    errors = summary.get("errors") or []
    lines = [
        f"Session: {session.label} ({session.session_id})",
        f"Log: {session.log_path}",
        f"Actions: {', '.join(summary.get('actions_taken') or [])}",
        f"Final phase: {final_state.get('phase', 'unknown')}",
        f"End reached: {yes_no(bool(summary.get('end_condition_reached')))}",
        f"Replay verified: {yes_no(bool(replay_result.get('verified')))}",
        f"Events replayed: {replay_result.get('events_replayed', 0)}",
        f"Physics preview shown: {physics_preview}",
        *environment_lines(summary.get("environment_review") or {}),
        f"Warnings: {len(warnings)}",
        *[f"  - {finding_text(finding)}" for finding in warnings],
        f"Errors: {len(errors)}",
        *[f"  - {finding_text(finding)}" for finding in errors],
        "Reminder: validation here is POC rule checking, not real emergency guidance.",
    ]
    return "\n".join(lines)


def finding_text(finding: dict[str, Any]) -> str:
    code = finding.get("code", "finding")
    message = finding.get("message", "No message")
    return f"{code}: {message}"


def environment_lines(environment_review: dict[str, Any]) -> list[str]:
    chair = environment_review.get("wooden_chair_poc")
    door = environment_review.get("entry_door_poc")
    lines: list[str] = []
    if chair:
        lines.extend(
            [
                "Environment: wooden chair",
                f"  - Blocked path at end: {yes_no(bool(chair.get('blocked_path')))}",
                f"  - Moved during scenario: {yes_no(bool(chair.get('moved')))}",
                f"  - Scenario physics flag: {yes_no(bool(chair.get('physics_enabled')))}",
                f"  - Gravity note: {chair.get('gravity_note')}",
            ]
        )
    if door:
        lines.extend(
            [
                "Environment: entry door",
                f"  - Open at end: {yes_no(bool(door.get('open')))}",
                f"  - Blocks path at end: {yes_no(bool(door.get('blocked_path')))}",
                f"  - Locked metadata: {yes_no(bool(door.get('locked')))}",
                f"  - Door type metadata: {door.get('door_type')}",
            ]
        )
    return lines or ["Environment: no environment object state found"]


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


async def run_demo(
    *,
    http_url: str,
    ws_url: str,
    session_prefix: str,
    physics_preview: PhysicsPreview,
    no_start_backend: bool,
    keep_backend_running: bool,
) -> int:
    started_process: subprocess.Popen[bytes] | None = None
    if is_backend_healthy(http_url):
        print(f"Backend detected at {http_url}")
    elif no_start_backend:
        print(f"Backend is not healthy at {http_url}; start it or remove --no-start-backend.")
        return 1
    else:
        print(f"Starting backend at {http_url}")
        started_process = start_backend(http_url)
        if not wait_for_backend(http_url):
            stop_backend(started_process)
            print("Backend did not become healthy in time.")
            return 1

    run_id = time.strftime("%Y%m%d-%H%M%S")
    sessions = build_demo_sessions(session_prefix, run_id)
    try:
        print()
        print(render_chair_preview(chair_previews(physics_preview)))
        for session in sessions:
            print()
            print(f"Running {session.label}: {session.session_id}")
            messages = await run_websocket_session(ws_url, session)
            print(f"Received {len(messages)} WebSocket messages")
            replay_result = replay(session.log_path)
            summary = generate_review_summary(session.log_path)
            print(
                render_review_report(
                    session=session,
                    summary=summary,
                    replay_result=replay_result,
                    physics_preview=physics_preview,
                )
            )
        return 0
    finally:
        if started_process is not None and not keep_backend_running:
            stop_backend(started_process)
            print()
            print("Stopped demo backend.")
        elif started_process is not None:
            print()
            print("Demo backend left running.")


def stop_backend(process: subprocess.Popen[bytes]) -> None:
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--http-url", default=DEFAULT_HTTP_URL)
    parser.add_argument("--ws-url")
    parser.add_argument("--no-start-backend", action="store_true")
    parser.add_argument("--keep-backend-running", action="store_true")
    parser.add_argument("--session-prefix", default="demo")
    parser.add_argument(
        "--physics-preview",
        choices=["disabled", "enabled", "both"],
        default="both",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    ws_url = arguments.ws_url or ws_url_from_http(arguments.http_url)
    return asyncio.run(
        run_demo(
            http_url=arguments.http_url,
            ws_url=ws_url,
            session_prefix=arguments.session_prefix,
            physics_preview=arguments.physics_preview,
            no_start_backend=arguments.no_start_backend,
            keep_backend_running=arguments.keep_backend_running,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
