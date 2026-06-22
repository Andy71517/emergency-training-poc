"""Single-process WebSocket session endpoint."""

from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from backend.app.models.messages import ErrorMessage, StartSessionMessage, TraineeActionMessage
from backend.app.orchestrator.session_manager import SessionInputError, SessionManager


def create_websocket_router(session_manager: SessionManager) -> APIRouter:
    router = APIRouter()

    @router.websocket("/ws/sessions/{session_id}")
    async def websocket_session(websocket: WebSocket, session_id: str) -> None:
        await websocket.accept()
        try:
            first_message = await websocket.receive_json()
            pending_action: dict[str, Any] | None = None
            if first_message.get("message_type") == "start_session":
                start = StartSessionMessage.model_validate(first_message)
                scenario_id = start.scenario_id
            elif first_message.get("message_type") == "trainee_action":
                scenario_id = first_message.get("scenario_id", "smoke_inhalation_room_v0")
                pending_action = first_message
            else:
                await _send_error(websocket, "invalid_initial_message", "Send start_session or trainee_action first.")
                await websocket.close(code=1008)
                return

            started = session_manager.start_session(session_id, scenario_id)
            await websocket.send_json(started.model_dump(mode="json"))

            if pending_action is not None:
                should_close = await _process_action(websocket, session_manager, session_id, pending_action)
                if should_close:
                    return

            while True:
                raw_message = await websocket.receive_json()
                if raw_message.get("message_type") != "trainee_action":
                    await _send_error(websocket, "unsupported_message", "Expected trainee_action message.")
                    continue
                should_close = await _process_action(websocket, session_manager, session_id, raw_message)
                if should_close:
                    return
        except WebSocketDisconnect:
            return
        except ValidationError as error:
            await _send_error(websocket, "invalid_message", _validation_message(error))
            await websocket.close(code=1008)
        except (SessionInputError, ValueError) as error:
            await _send_error(websocket, "session_error", str(error))
            await websocket.close(code=1008)

    return router


async def _process_action(
    websocket: WebSocket,
    session_manager: SessionManager,
    session_id: str,
    raw_message: dict[str, Any],
) -> bool:
    try:
        message = TraineeActionMessage.model_validate(raw_message)
        processed = session_manager.process_action(session_id, message)
    except ValidationError as error:
        await _send_error(websocket, "invalid_message", _validation_message(error))
        return False
    except SessionInputError as error:
        await _send_error(websocket, "session_error", str(error))
        return False

    await websocket.send_json(processed.update.model_dump(mode="json"))
    if processed.ended is not None:
        await websocket.send_json(processed.ended.model_dump(mode="json"))
        await websocket.close(code=1000)
        return True
    return False


async def _send_error(websocket: WebSocket, code: str, message: str) -> None:
    payload = ErrorMessage(code=code, message=message)
    await websocket.send_json(payload.model_dump(mode="json"))


def _validation_message(error: ValidationError) -> str:
    first = error.errors()[0]
    location = ".".join(str(item) for item in first["loc"])
    return f"{location}: {first['msg']}"
