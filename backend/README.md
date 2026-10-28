# Backend

FastAPI owns the local API, deterministic session state, persistent studio jobs,
asset packages and trusted worker orchestration. [Current status](../docs/current-status.md).

## Services

| Area | Responsibility and storage |
| --- | --- |
| `app/api/` | Health, session WebSocket, legacy demo/authoring, physics, room studio and furniture routes |
| `app/studio/` | Hosted planning, seeded layouts, SQLite jobs/assets, history, Blender/editor work and recordings under ignored `logs/studio/` |
| `app/studio/asset_automation.py` | Saved description dispatches, same-job recovery, retrieved-package validation and preparation |
| `app/studio/arc_transport.py` | Fixed verified noninteractive SSH RPC; no browser-supplied commands or credentials |
| `blender_mcp.py` | Real stdio MCP server with bounded `inspect_asset` / `prepare_asset` tools; background Blender and CPU collision processing |
| `app/physics/` | Authorizes the browser primitive proof and records observations under `logs/physics/` |
| `app/orchestrator/`, `scenario_engine/`, `validation/` | In-memory deterministic sessions, ordered actions and toy-rule findings |
| `app/authoring/` | Separate in-memory fixture authoring/revision approval; still mocked |
| `app/logging/` | JSONL session records and replay/review support under `logs/sessions/` |

## Run from the repository root

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
npm.cmd --prefix web ci
.\.venv\Scripts\python.exe scripts/run_web_demo.py --port 8772
```

For backend-only development, run FastAPI on port 8765; Vite proxies to that port:

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765
``` Avoid reload/multiple workers
during persistent jobs. Preserve `backend/.env`, `arc/.env` and ignored saved data.
See [workspace setup](../docs/arc-workspace-runbook.md) and
[asset automation](../docs/asset-automation-runbook.md).

`GET /health` checks the app. Hosted planner and SSH GPU worker connection checks
are separate actions. A configuration flag is not connectivity or generation evidence.
The session WebSocket defaults to `smoke_inhalation_room_v0`; the first
`start_session` message may select another checked-in scenario.

## Trust boundary

The backend checks message shape, IDs, sequence, duplication and bounded payloads.
Studio routes restrict foreign origins; artifact routes derive scoped paths, validate
package hashes and keep keys out of child environments. SSH host checking remains on.
MCP tools run fixed scripts, not arbitrary model-generated Python.

This is still an unauthenticated single-user loopback app, not production access
control. Model plans, imported models and client/engine observations need validation
and review. [Security](../docs/security/README.md), [API map](app/api/README.md),
[tests](tests/README.md).
