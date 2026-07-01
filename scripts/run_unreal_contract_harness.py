"""Exercise the WebSocket contract as a future thin Unreal client would.

This harness does not render, simulate gameplay, validate responders, or own scenario
logic. It only checks the client-side connection lifecycle and message ordering.
"""

import argparse
import asyncio
import json
from enum import Enum
from typing import Any

import websockets

from backend.app.adapters.manual_input_adapter import build_action_message


DEFAULT_ACTIONS = [
    "assess_scene",
    "confirm_ppe",
    "request_backup",
    "move_obstacle",
    "enter_room",
    "remove_occupant",
]


class ClientPhase(str, Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    WAITING_FOR_SESSION_STARTED = "WAITING_FOR_SESSION_STARTED"
    READY_FOR_ACTION = "READY_FOR_ACTION"
    WAITING_FOR_STATE_UPDATE = "WAITING_FOR_STATE_UPDATE"
    WAITING_FOR_SCENARIO_END = "WAITING_FOR_SCENARIO_END"
    ENDED = "ENDED"
    ERROR = "ERROR"


class ContractHarnessError(RuntimeError):
    """Raised when backend messages violate the thin client lifecycle."""


class UnrealClientStateMachine:
    """Minimal lifecycle guard for a future Unreal presentation client."""

    def __init__(self) -> None:
        self.phase = ClientPhase.DISCONNECTED

    def begin_connect(self) -> None:
        self._require(ClientPhase.DISCONNECTED)
        self.phase = ClientPhase.CONNECTING

    def socket_opened(self) -> None:
        self._require(ClientPhase.CONNECTING)
        self.phase = ClientPhase.WAITING_FOR_SESSION_STARTED

    def action_sent(self) -> None:
        self._require(ClientPhase.READY_FOR_ACTION)
        self.phase = ClientPhase.WAITING_FOR_STATE_UPDATE

    def handle_server_message(self, message: dict[str, Any]) -> None:
        message_type = message.get("message_type")
        if message_type == "error":
            self.phase = ClientPhase.ERROR
            return

        if message_type == "session_started":
            self._require(ClientPhase.WAITING_FOR_SESSION_STARTED)
            self.phase = ClientPhase.READY_FOR_ACTION
            return

        if message_type == "scenario_state_update":
            self._require(ClientPhase.WAITING_FOR_STATE_UPDATE)
            scenario_state = message.get("scenario_state", {})
            self.phase = (
                ClientPhase.WAITING_FOR_SCENARIO_END
                if scenario_state.get("is_terminal") is True
                else ClientPhase.READY_FOR_ACTION
            )
            return

        if message_type == "scenario_ended":
            self._require(ClientPhase.WAITING_FOR_SCENARIO_END)
            self.phase = ClientPhase.ENDED
            return

        raise ContractHarnessError(f"Unsupported server message type: {message_type!r}")

    def _require(self, expected: ClientPhase) -> None:
        if self.phase != expected:
            raise ContractHarnessError(f"Expected phase {expected}, got {self.phase}.")


async def run_contract_session(
    *,
    base_url: str,
    session_id: str,
    scenario_id: str,
    actions: list[str],
) -> list[dict[str, Any]]:
    """Run a scripted contract session and return received backend messages."""

    uri = f"{base_url.rstrip('/')}/ws/sessions/{session_id}"
    state_machine = UnrealClientStateMachine()
    received: list[dict[str, Any]] = []

    state_machine.begin_connect()
    print(f"[contract] connecting: {uri}")
    async with websockets.connect(uri) as websocket:
        state_machine.socket_opened()
        await websocket.send(json.dumps({"message_type": "start_session", "scenario_id": scenario_id}))
        started = json.loads(await websocket.recv())
        state_machine.handle_server_message(started)
        received.append(started)
        print_message(started, state_machine.phase)

        for sequence_number, action_type in enumerate(actions, start=1):
            message = build_action_message(
                session_id=session_id,
                scenario_id=scenario_id,
                action_type=action_type,
                sequence_number=sequence_number,
                actor_id="future-unreal-client",
            )
            state_machine.action_sent()
            print(f"[contract] -> trainee_action:{action_type} seq={sequence_number}")
            await websocket.send(message.model_dump_json())

            update = json.loads(await websocket.recv())
            state_machine.handle_server_message(update)
            received.append(update)
            print_message(update, state_machine.phase)

            if state_machine.phase == ClientPhase.WAITING_FOR_SCENARIO_END:
                ended = json.loads(await websocket.recv())
                state_machine.handle_server_message(ended)
                received.append(ended)
                print_message(ended, state_machine.phase)
                break

        if state_machine.phase not in {ClientPhase.READY_FOR_ACTION, ClientPhase.ENDED}:
            raise ContractHarnessError(f"Session stopped in unexpected phase {state_machine.phase}.")

    return received


def print_message(message: dict[str, Any], phase: ClientPhase) -> None:
    message_type = message.get("message_type")
    if message_type == "scenario_state_update":
        validation = message["validation_result"]
        state = message["scenario_state"]
        print(
            "[contract] <- scenario_state_update "
            f"seq={message['sequence_number']} "
            f"terminal={state['is_terminal']} "
            f"validation={validation['status']} "
            f"phase={phase.value}"
        )
        return

    print(f"[contract] <- {message_type} phase={phase.value}")


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="ws://127.0.0.1:8000")
    parser.add_argument("--session-id", default="unreal-contract-harness")
    parser.add_argument("--scenario-id", default="smoke_inhalation_room_v0")
    parser.add_argument("--actions", nargs="*", default=DEFAULT_ACTIONS)
    arguments = parser.parse_args()

    await run_contract_session(
        base_url=arguments.url,
        session_id=arguments.session_id,
        scenario_id=arguments.scenario_id,
        actions=arguments.actions,
    )


if __name__ == "__main__":
    asyncio.run(main())
