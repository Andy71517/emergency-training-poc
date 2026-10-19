"""Run a presentation-friendly menu for the deterministic local POC.

This script is a local demo helper, not real emergency-response guidance. Its
reviews explain deterministic POC rule checks and recorded state only.
"""

import argparse
import asyncio
import json
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

import websockets

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.adapters.manual_input_adapter import build_action_message
from backend.app.demo_catalog import (
    DEMO_DEFINITIONS,
    DemoDefinition,
)
from backend.app.logging.review_summary import generate_review_summary
from backend.app.scenario_engine.loader import load_scenario
from scripts.replay_session import replay
from scripts.run_local_demo import (
    DEFAULT_HTTP_URL,
    DEFAULT_LOG_DIRECTORY,
    is_backend_healthy,
    make_session_id,
    start_backend,
    stop_backend,
    wait_for_backend,
    ws_url_from_http,
)

DISCLAIMER = (
    "POC rule checks only — not clinical validation, operational guidance, or protocol authority."
)

STATUS_LABELS = {
    "ok": "Accepted",
    "warning": "Review suggested",
    "error": "Action not accepted",
}


def available_scenarios() -> list[tuple[str, str, tuple[str, ...]]]:
    """Return small, readable scenario details from the checked-in fixtures."""

    scenarios: list[tuple[str, str, tuple[str, ...]]] = []
    for path in sorted((REPO_ROOT / "scenarios").glob("*.yaml")):
        scenario = load_scenario(path.stem)
        scenarios.append((scenario.scenario_id, scenario.title, scenario.allowed_actions))
    return scenarios


def session_logs(log_directory: Path = DEFAULT_LOG_DIRECTORY) -> list[Path]:
    """List local session logs newest first, ignoring directories and unrelated files."""

    if not log_directory.is_dir():
        return []
    return sorted(
        (path for path in log_directory.glob("*.jsonl") if path.is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def parse_action_list(value: str) -> list[str]:
    """Turn a comma-separated custom action entry into action names."""

    return [action.strip() for action in value.split(",") if action.strip()]


def render_health_status(http_url: str) -> str:
    """Render a short, presentation-safe backend status line."""

    try:
        with urlopen(f"{http_url.rstrip('/')}/health", timeout=1.0) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return (
            "Backend status\n"
            f"  - URL: {http_url}\n"
            f"  - Health: {payload.get('status', 'unknown')}\n"
            f"  - Service: {payload.get('service', 'unknown')}\n"
            f"  - {DISCLAIMER}"
        )
    except (OSError, URLError, TimeoutError, json.JSONDecodeError):
        return (
            "Backend status\n"
            f"  - URL: {http_url}\n"
            "  - Health: unavailable\n"
            "  - Start the backend, or run a demo option and let this menu start it."
        )


def render_scenario_list() -> str:
    lines = ["Current deterministic POC scenarios:"]
    for scenario_id, title, allowed_actions in available_scenarios():
        lines.extend(
            [
                f"  - {title.removeprefix('POC: ')}",
                f"    Actions: {', '.join(friendly_label(action) for action in allowed_actions)}",
            ]
        )
    lines.append(f"  - {DISCLAIMER}")
    return "\n".join(lines)


def friendly_label(value: Any) -> str:
    """Turn an internal identifier into a label suitable for a live demo."""

    if value is None:
        return "Unknown"
    label = str(value).replace("_v0", "").replace("_poc", "").replace("_", " ").strip().capitalize()
    return label.replace(" ppe", " PPE")


def scenario_title(scenario_id: str | None) -> str:
    for current_id, title, _ in available_scenarios():
        if current_id == scenario_id:
            return title.removeprefix("POC: ")
    return friendly_label(scenario_id)


def cue_summary_lines(environment: dict[str, Any]) -> list[str]:
    """Describe useful final cues without exposing backend field names."""

    cues = environment.get("room_cues") or {}
    checks = {
        "area check": bool(cues.get("room_scanned")),
        "door check": bool(cues.get("door_checked")),
        "status communication": bool(cues.get("status_communicated")),
        "environment monitoring": bool(cues.get("environment_monitored")),
        "clear exit path": bool(cues.get("exit_path_clear")),
    }
    if cues.get("occupant_removed"):
        occupant_text = "removed from the room"
    elif cues.get("occupant_guided"):
        occupant_text = "guided to the exit"
    elif cues.get("occupant_located"):
        occupant_text = "located"
    else:
        occupant_text = "not completed"
    completed = ", ".join(label for label, complete in checks.items() if complete) or "none"
    missing = ", ".join(label for label, complete in checks.items() if not complete) or "none"
    return [
        f"  - Completed: {completed}",
        f"  - Still missing: {missing}",
        f"  - Occupant handling: {occupant_text}",
    ]


def menu_finding_lines(summary: dict[str, Any]) -> list[str]:
    """Return unique plain-English findings while hiding internal rule codes."""

    findings = (summary.get("errors") or []) + (summary.get("warnings") or [])
    lines: list[str] = []
    seen: set[str] = set()
    for finding in findings:
        message = str(finding.get("message") or "A toy scenario rule flagged this action for review.")
        if message in seen:
            continue
        seen.add(message)
        lines.append(f"  - {message}")
    return lines


def format_menu_review(
    summary: dict[str, Any],
    *,
    replay_result: dict[str, Any] | None = None,
    show_action_details: bool = False,
) -> str:
    """Render the short, plain-English review used by the presentation menu."""

    timeline = summary.get("action_timeline") or []
    action_story = ", ".join(friendly_label(item.get("action_type")) for item in timeline)
    issue_counts: dict[tuple[str, str], int] = {}
    for item in timeline:
        if item.get("validation_status") not in {"warning", "error"}:
            continue
        key = (
            friendly_label(item.get("action_type")),
            STATUS_LABELS.get(str(item.get("validation_status")), "Needs review"),
        )
        issue_counts[key] = issue_counts.get(key, 0) + 1
    result = (
        "End condition reached"
        if summary.get("end_condition_reached")
        else "Run stopped before the end condition"
    )
    lines = [
        "\nDEMO REVIEW",
        f"Scenario: {scenario_title(summary.get('scenario_id'))}",
        f"Result: {result}",
        f"Summary: {summary.get('review_headline', 'No summary was generated.')}",
    ]
    if replay_result is not None:
        replay_text = "yes" if replay_result.get("verified") else "no"
        lines.append(f"Saved log replayed successfully: {replay_text}")

    lines.extend(["", f"Actions recorded: {len(timeline)}"])
    if show_action_details:
        lines.extend(["Action sequence:", f"  {action_story or 'No actions recorded.'}"])
    else:
        lines.append("  Full sequence hidden to keep the presentation focused.")
    if issue_counts:
        lines.extend(["", "Actions to discuss:"])
        for (action, status), count in issue_counts.items():
            repeat = f" ({count} times)" if count > 1 else ""
            lines.append(f"  - {action}: {status}{repeat}")

    progress_stories = summary.get("progress_stories") or []
    if progress_stories:
        lines.extend(["", "What changed before the retry:"])
        lines.extend(f"  - {story}" for story in progress_stories)

    lines.extend(["", "Important cues at the end:"])
    lines.extend(cue_summary_lines(summary.get("environment_review") or {}))

    findings = menu_finding_lines(summary)
    lines.extend(["", "Discussion points:"])
    lines.extend(findings or ["  - No warnings or errors were recorded by the toy rules."])
    instructor_review = summary.get("instructor_review") or {}
    if instructor_review:
        lines.extend(
            [
                "",
                str(instructor_review.get("title") or "Instructor review message"),
                f"  {instructor_review.get('summary')}",
            ]
        )
        lines.extend(f"  - {item}" for item in instructor_review.get("evidence") or [])
        lines.append(f"  Discussion prompt: {instructor_review.get('discussion_prompt')}")
        lines.append(f"  Boundary: {instructor_review.get('boundary')}")
    lines.extend(["", DISCLAIMER])
    return "\n".join(lines)


def wants_yes(response: str, *, default: bool) -> bool:
    """Interpret a small yes/no menu response."""

    normalized = response.strip().lower()
    if not normalized:
        return default
    return normalized in {"y", "yes"}


def render_session_comparison(
    first: dict[str, Any],
    second: dict[str, Any],
    *,
    first_label: str,
    second_label: str,
) -> str:
    """Compare two saved reviews without claiming a trainee-performance score."""

    lines = ["Session comparison", f"  - {first_label}: {comparison_line(first)}", f"  - {second_label}: {comparison_line(second)}"]
    if first.get("scenario_id") != second.get("scenario_id"):
        lines.append("  - Note: these runs use different toy scenarios, so compare the review story, not scores.")
    else:
        warning_difference = len(second.get("warnings") or []) - len(first.get("warnings") or [])
        error_difference = len(second.get("errors") or []) - len(first.get("errors") or [])
        lines.append(
            "  - Difference: "
            f"warnings {signed_difference(warning_difference)}, "
            f"errors {signed_difference(error_difference)}."
        )
    lines.append(f"  - {DISCLAIMER}")
    return "\n".join(lines)


def comparison_line(summary: dict[str, Any]) -> str:
    return (
        f"{scenario_title(summary.get('scenario_id'))}; "
        f"end reached: {'yes' if summary.get('end_condition_reached') else 'no'}; "
        f"{summary.get('total_actions', 0)} actions; "
        f"{len(summary.get('warnings') or [])} warnings; "
        f"{len(summary.get('errors') or [])} errors"
    )


def signed_difference(value: int) -> str:
    return f"+{value}" if value > 0 else str(value)


async def run_session(
    *,
    ws_url: str,
    definition: DemoDefinition,
    session_id: str,
    output: Callable[[str], None] = print,
) -> Path:
    """Run one deterministic action sequence and print only concise live updates."""

    uri = f"{ws_url.rstrip('/')}/ws/sessions/{session_id}"
    log_path = DEFAULT_LOG_DIRECTORY / f"{session_id}.jsonl"
    output(f"\nRunning: {definition.label}")
    output(f"Scenario: {scenario_title(definition.scenario_id)}")
    output(f"Running {len(definition.actions)} scripted actions...")
    async with websockets.connect(uri) as websocket:
        await websocket.send(
            json.dumps({"message_type": "start_session", "scenario_id": definition.scenario_id})
        )
        started = json.loads(await websocket.recv())
        if started.get("message_type") == "error":
            raise RuntimeError(started.get("message", "The backend could not start the session."))

        for sequence_number, action_type in enumerate(definition.actions, start=1):
            message = build_action_message(
                session_id=session_id,
                scenario_id=definition.scenario_id,
                action_type=action_type,
                sequence_number=sequence_number,
            )
            await websocket.send(message.model_dump_json())
            update = json.loads(await websocket.recv())
            if update.get("message_type") == "error":
                continue
            if (update.get("scenario_state") or {}).get("is_terminal"):
                await websocket.recv()  # scenario_ended message
                break
    return log_path


def print_review(
    log_path: Path,
    output: Callable[[str], None] = print,
    *,
    show_action_details: bool = False,
) -> dict[str, Any]:
    """Print replay verification and a full instructor-facing review."""

    replay_result = replay(log_path)
    summary = generate_review_summary(log_path)
    output("")
    output(
        format_menu_review(
            summary,
            replay_result=replay_result,
            show_action_details=show_action_details,
        )
    )
    return summary


def replay_or_saved_review(
    log_path: Path,
    output: Callable[[str], None] = print,
) -> dict[str, Any]:
    """Replay compatible logs, while keeping older saved reviews readable."""

    try:
        replay_result = replay(log_path)
    except ValueError as error:
        if "Replay mismatch" not in str(error):
            raise
        summary = generate_review_summary(log_path)
        output(
            "This older log cannot be strictly replayed against the current scenario version. "
            "Its saved review is still available below."
        )
        output(format_menu_review(summary))
        return {"verified": False, "saved_review_available": True}

    output(
        f"Replay verified {replay_result['events_replayed']} events. "
        "The saved actions still reproduce the recorded final state."
    )
    return replay_result


def offer_action_details(
    summary: dict[str, Any],
    input_fn: Callable[[str], str],
    output: Callable[[str], None] = print,
) -> None:
    """Optionally show the full action sequence after the concise review."""

    response = input_fn("Show the full action sequence? [y/N]: ")
    if wants_yes(response, default=False):
        timeline = summary.get("action_timeline") or []
        story = ", ".join(friendly_label(item.get("action_type")) for item in timeline)
        output(f"\nAction sequence:\n  {story or 'No actions recorded.'}")


def choose_log(
    input_fn: Callable[[str], str],
    output: Callable[[str], None] = print,
) -> Path | None:
    logs = session_logs()
    if not logs:
        output("No local session logs found yet. Run a demo first.")
        return None
    output("\nSaved session logs:")
    for index, path in enumerate(logs, start=1):
        output(f"  {index}. {path.name}")
    choice = input_fn("Choose a log number (or press Enter to cancel): ").strip()
    if not choice:
        return None
    try:
        return logs[int(choice) - 1]
    except (ValueError, IndexError):
        output("That was not a log in the list.")
        return None


def choose_scenario(
    input_fn: Callable[[str], str],
    output: Callable[[str], None] = print,
) -> tuple[str, tuple[str, ...]] | None:
    scenarios = available_scenarios()
    output("\nChoose a toy scenario for custom actions:")
    for index, (scenario_id, title, _) in enumerate(scenarios, start=1):
        output(f"  {index}. {title} ({scenario_id})")
    choice = input_fn("Scenario number (or press Enter to cancel): ").strip()
    if not choice:
        return None
    try:
        scenario_id, _, allowed_actions = scenarios[int(choice) - 1]
        return scenario_id, allowed_actions
    except (ValueError, IndexError):
        output("That was not a scenario in the list.")
        return None


async def run_definition_with_review(
    definition: DemoDefinition,
    *,
    ws_url: str,
    session_prefix: str,
    fast: bool,
    demo_delay: float,
    input_fn: Callable[[str], str] = input,
    output: Callable[[str], None] = print,
) -> Path:
    run_id = time.strftime("%Y%m%d-%H%M%S")
    label = definition.label.replace(" path", "").replace(" ", "-")
    session_id = make_session_id(session_prefix, label, run_id)
    if not fast and demo_delay > 0:
        output(f"\nPresentation pacing: pausing for {demo_delay:g} second(s) before the run.")
        await asyncio.sleep(demo_delay)
    log_path = await run_session(
        ws_url=ws_url,
        definition=definition,
        session_id=session_id,
        output=output,
    )
    summary = print_review(log_path, output, show_action_details=fast)
    if not fast:
        offer_action_details(summary, input_fn, output)
    return log_path


async def run_all_demos(
    *,
    ws_url: str,
    session_prefix: str,
    fast: bool,
    demo_delay: float,
    input_fn: Callable[[str], str] = input,
    output: Callable[[str], None] = print,
) -> list[Path]:
    log_paths: list[Path] = []
    for index, definition in enumerate(DEMO_DEFINITIONS):
        log_paths.append(
            await run_definition_with_review(
                definition,
                ws_url=ws_url,
                session_prefix=session_prefix,
                fast=fast,
                demo_delay=demo_delay,
                input_fn=input_fn,
                output=output,
            )
        )
        if not fast and index < len(DEMO_DEFINITIONS) - 1:
            next_demo = DEMO_DEFINITIONS[index + 1].label
            response = input_fn(f"\nContinue to {next_demo}? [Y/n]: ")
            if not wants_yes(response, default=True):
                output("Run-all stopped. Completed reviews and logs were kept.")
                break
    return log_paths


def ensure_backend(
    http_url: str, *, no_start_backend: bool, output: Callable[[str], None] = print
) -> Any | None:
    if is_backend_healthy(http_url):
        output(f"Using backend already running at {http_url}.")
        return None
    if no_start_backend:
        output("Backend is unavailable. Start it, or remove --no-start-backend.")
        return False
    output(f"Starting local backend at {http_url}.")
    process = start_backend(http_url)
    if wait_for_backend(http_url):
        return process
    stop_backend(process)
    output("The backend did not become healthy in time.")
    return False


async def interactive_menu(arguments: argparse.Namespace) -> int:
    ws_url = arguments.ws_url or ws_url_from_http(arguments.http_url)
    backend_process = ensure_backend(arguments.http_url, no_start_backend=arguments.no_start_backend)
    if backend_process is False:
        return 1

    if arguments.fast:
        print("Developer mode: no intentional delay or between-run prompts; action details are shown.")
    else:
        print(
            "Presentation mode: concise reviews, optional action details, and a brief announced "
            "pause before each run."
        )

    try:
        while True:
            print(
                "\nEmergency Training POC — menu demo\n"
                "  1. Run smoke-room happy path\n"
                "  2. Run smoke-room warning/error path\n"
                "  3. Run blocked-exit hallway happy path\n"
                "  4. Run blocked-exit hallway warning path\n"
                "  5. Run all demo sessions\n"
                "  6. Replay a previous session log\n"
                "  7. Summarize a previous session log\n"
                "  8. Compare two session logs\n"
                "  9. Show backend health/status\n"
                " 10. Show current scenario list\n"
                " 11. Run custom action mode\n"
                "  0. Exit\n"
                f"  {DISCLAIMER}"
            )
            choice = input("Choose an option: ").strip()
            if choice == "0":
                return 0
            if choice in {"1", "2", "3", "4"}:
                await run_definition_with_review(
                    DEMO_DEFINITIONS[int(choice) - 1],
                    ws_url=ws_url,
                    session_prefix=arguments.session_prefix,
                    fast=arguments.fast,
                    demo_delay=arguments.demo_delay,
                )
            elif choice == "5":
                await run_all_demos(
                    ws_url=ws_url,
                    session_prefix=arguments.session_prefix,
                    fast=arguments.fast,
                    demo_delay=arguments.demo_delay,
                )
            elif choice == "6":
                log_path = choose_log(input)
                if log_path is not None:
                    replay_or_saved_review(log_path)
            elif choice == "7":
                log_path = choose_log(input)
                if log_path is not None:
                    summary = print_review(log_path, show_action_details=arguments.fast)
                    if not arguments.fast:
                        offer_action_details(summary, input)
            elif choice == "8":
                print("Choose the first session to compare.")
                first_path = choose_log(input)
                print("Choose the second session to compare.")
                second_path = choose_log(input)
                if first_path is not None and second_path is not None:
                    print(
                        render_session_comparison(
                            generate_review_summary(first_path),
                            generate_review_summary(second_path),
                            first_label=first_path.name,
                            second_label=second_path.name,
                        )
                    )
            elif choice == "9":
                print(render_health_status(arguments.http_url))
            elif choice == "10":
                print(render_scenario_list())
            elif choice == "11":
                selection = choose_scenario(input)
                if selection is not None:
                    scenario_id, allowed_actions = selection
                    print(f"Allowed action names: {', '.join(allowed_actions)}")
                    raw_actions = input("Comma-separated actions (include stop_scenario if desired): ")
                    actions = parse_action_list(raw_actions)
                    if not actions:
                        print("No actions entered; custom run canceled.")
                    else:
                        await run_definition_with_review(
                            DemoDefinition(
                                demo_id="custom-action-run",
                                label="Custom action run",
                                short_label="Custom action run",
                                scenario_id=scenario_id,
                                tone="custom",
                                description="A locally entered deterministic action sequence.",
                                actions=tuple(actions),
                            ),
                            ws_url=ws_url,
                            session_prefix=arguments.session_prefix,
                            fast=arguments.fast,
                            demo_delay=arguments.demo_delay,
                        )
            else:
                print("Please choose one of the listed numbers.")
    except (OSError, ValueError, RuntimeError, websockets.WebSocketException) as error:
        print(f"Menu action could not finish: {error}")
        return 1
    finally:
        if backend_process is not None:
            stop_backend(backend_process)
            print("Stopped the local demo backend.")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--http-url", default=DEFAULT_HTTP_URL)
    parser.add_argument("--ws-url")
    parser.add_argument("--no-start-backend", action="store_true")
    parser.add_argument("--session-prefix", default="menu-demo")
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Use developer mode: no intentional delay or between-run prompts.",
    )
    parser.add_argument(
        "--demo-delay",
        type=float,
        default=2.5,
        help="Presentation-mode pause before each run in seconds (default: 2.5).",
    )
    return parser.parse_args()


def main() -> int:
    return asyncio.run(interactive_menu(parse_arguments()))


if __name__ == "__main__":
    raise SystemExit(main())
