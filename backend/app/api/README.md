# API layer

FastAPI routes expose validated actions and scoped artifacts. Domain rules and
worker orchestration live in their services, not in browser input.

| Module | Route family / purpose |
| --- | --- |
| `health.py` | `GET /health` |
| `websocket_sessions.py` | `/ws/sessions/{session_id}` ordered deterministic sessions |
| `demo.py` | `/api/demo` legacy paths and review helpers |
| `authoring.py` | `/api/authoring` fixture drafts and revision-bound approval |
| `physics.py` | `/api/physics/proof` primitive proof authorization/observations |
| `studio.py` | `/api/studio` room jobs, configuration, history, workers and evidence |
| `assets.py` | `/api/studio/assets` designs, request/result packages, preparation and artifacts |
| `assets.py` automation routes | `/api/studio/assets/automation/{config,check,jobs}` and `/jobs/{id}/resume` |

Hosted planner checks and GPU SSH worker checks are distinct. They must not return
secrets or infer generation success from configuration. Studio actions reject
foreign origins, constrain uploads and derive allowed artifact paths. The app is
still a loopback single-user POC without authentication or multi-user authorization.

[Backend guide](../../README.md), [security](../../../docs/security/README.md),
[asset automation](../../../docs/asset-automation-runbook.md).

For repository-wide implementation and evidence, see [current status](../../../docs/current-status.md)
and the [documentation index](../../../docs/README.md).
