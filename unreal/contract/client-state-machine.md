# Minimal Client-Side State Machine

This state machine is only for the future Unreal client shell.

Its job is to keep message order clean. It does not implement scenario logic.

```text
DISCONNECTED
  -> CONNECTING
  -> WAITING_FOR_SESSION_STARTED
  -> READY_FOR_ACTION
  -> WAITING_FOR_STATE_UPDATE
  -> READY_FOR_ACTION
  -> WAITING_FOR_STATE_UPDATE
  -> WAITING_FOR_SCENARIO_END
  -> ENDED
```

Any backend `error` message moves the client to `ERROR`.

## States

| State | Meaning | Allowed client action |
| --- | --- | --- |
| `DISCONNECTED` | No socket is open. | Open a WebSocket. |
| `CONNECTING` | The socket is opening. | Wait. |
| `WAITING_FOR_SESSION_STARTED` | `start_session` has been sent. | Wait for `session_started`. |
| `READY_FOR_ACTION` | The backend has sent the current state. | Send one `trainee_action`. |
| `WAITING_FOR_STATE_UPDATE` | One action is in flight. | Wait for `scenario_state_update`. |
| `WAITING_FOR_SCENARIO_END` | The backend reported terminal state. | Wait for `scenario_ended`. |
| `ENDED` | Session is complete. | Close or return to menu. |
| `ERROR` | Backend rejected the session/message. | Stop sending actions; open a new session if needed. |

## Important boundary

The client can decide what UI to show, but it must not invent scenario progress. `scenario_state_update` and `scenario_ended` are the only source of scenario progress.
