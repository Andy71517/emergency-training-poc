# FIELDWORK web app

React, TypeScript, Vite and Tailwind present the local scenario studio and asset
library. FastAPI owns jobs, accepted plans, session state and saved evidence.
[Current status](../docs/current-status.md).

## Current surfaces

- **Create scenario:** hosted ARC room planning, validated seeded chair layouts,
  previews, saved batches and replay with a different seed.
- **Asset library:** chair/couch designs; description-based ARC generation with
  persistent progress/reconnection; optional PNG/request/result ZIP route; actual
  GLB inspection and Blender MCP preparation downloads.
- **Pipeline stages / Connections:** background Blender rooms, editor bridge,
  Unreal assembly/Chaos reports, saved recordings and private local worker paths.
- **Recent batches / Trash:** exact-input reuse and recoverable deletion; files
  and external Unreal maps are retained.
- **Legacy POC tools:** guided/user-controlled deterministic sessions, seeded
  exploration, review/replay, fixture authoring and the primitive Rapier physics lab.

The hosted room planner is real. The legacy authoring suggestion remains a labeled
fixture. A generated furniture review candidate is not automatically eligible for
the existing chair-only room planner. See the [asset runbook](../docs/asset-automation-runbook.md).

## One-port app

From the repository root after installing the backend and Node dependencies:

```powershell
npm.cmd --prefix web ci
.\.venv\Scripts\python.exe scripts/run_web_demo.py --port 8772
```

Open `http://127.0.0.1:8772`. FastAPI serves `web/dist` and the API on the same origin.
Omitting `--port` uses the helper's default 8765. Do not stop an unrelated app if
that port is occupied. A build alone does not start the backend.

## Frontend development

Run FastAPI on 127.0.0.1:8765, then `npm.cmd --prefix web run dev` in another terminal.
Vite prints its URL (normally 5173) and proxies `/api`, `/health` and `/ws` to 8765.
This proxy does not follow the one-port app's `--port` option.

```powershell
npm.cmd --prefix web run lint
npm.cmd --prefix web run build
```

Node 22.13+ within the 22.x line matches the Vite/ESLint engine requirements and CI. Use `npm ci` for the checked-in lockfile; PowerShell users can
use `npm.cmd` to avoid script-execution-policy issues. Large physics chunks produce
a size advisory, not a failed build.

## Evidence and privacy

Browser Rapier runs a primitive rigid-body proof and sends observations to the
backend. Unreal Chaos is a separate engine workflow. Neither establishes clinical
validity or calibrated real-world physics. Saved Blender renders and MP4s can be
viewed without open editors; there is no live Unreal browser stream.

Passwords, Duo, SSH private keys and passphrases never belong in frontend fields.
The hosted model key stays backend-only. Keep this single-user app on loopback.
[Security](../docs/security/README.md), [room guide](../docs/studio-pipeline-runbook.md).
