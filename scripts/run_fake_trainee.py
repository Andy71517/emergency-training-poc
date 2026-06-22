"""Run two manual/stubbed action sequences against the local POC WebSocket."""

import argparse
import asyncio
import json
from typing import Any

import websockets

from backend.app.adapters.manual_input_adapter import build_action_message


async def run_session(base_url: str, session_id: str, actions: list[str]) -> None:
    uri = f"{base_url.rstrip('/')}/ws/sessions/{session_id}"
    print(f"\n[{session_id}] connecting to {uri}")
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"message_type": "start_session"}))
        print_received(json.loads(await websocket.recv()))

        for sequence_number, action_type in enumerate(actions, start=1):
            message = build_action_message(
                session_id=session_id,
                action_type=action_type,
                sequence_number=sequence_number,
            )
            print(f"[{session_id}] -> {action_type}")
            await websocket.send(message.model_dump_json())
            response = json.loads(await websocket.recv())
            print_received(response)
            if response.get("scenario_state", {}).get("is_terminal"):
                print_received(json.loads(await websocket.recv()))
                break


def print_received(message: dict[str, Any]) -> None:
    message_type = message.get("message_type")
    if message_type == "scenario_state_update":
        validation = message["validation_result"]
        state = message["scenario_state"]["state"]
        print(
            f"  <- state={state['phase']} validation={validation['status']} "
            f"warnings={len(validation['warnings'])} errors={len(validation['errors'])}"
        )
    else:
        print(f"  <- {message_type}: {json.dumps(message, sort_keys=True)}")


async def main(base_url: str) -> None:
    await run_session(
        base_url,
        "demo-happy",
        ["assess_scene", "confirm_ppe", "request_backup", "enter_room", "remove_occupant"],
    )
    await run_session(
        base_url,
        "demo-warning-error",
        ["confirm_ppe", "enter_room", "assess_scene", "stop_scenario"],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="ws://127.0.0.1:8000")
    arguments = parser.parse_args()
    asyncio.run(main(arguments.url))
