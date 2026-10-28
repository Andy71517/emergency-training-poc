# Local FIELDWORK workspace setup

Use `main`. The local web app owns planning, persistent layout review, asset jobs
and fixed Blender/Unreal controls. ARC hosts the model service and queued GPU work;
the workstation runs Blender and the Unreal editor. [Evidence](current-status.md).

## First installation on Windows

Install Git, Python 3.11+ and Node 22.13+ within the 22.x line. From a folder for a new checkout:

```powershell
git clone --branch main https://github.com/Andy71517/emergency-training-poc.git emergency-training-studio
cd emergency-training-studio
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
npm.cmd --prefix web ci
Copy-Item backend\.env.example backend\.env
notepad backend\.env
```

Only copy the template on a fresh installation. Preserve an existing private file.
Set the hosted planner key/model locally, configure the actual Blender executable
and reviewed `CHAIR_BLEND` when using room workers. Add the verified SSH target and
remote checkout for asset jobs using the [automation guide](asset-automation-runbook.md).
These are independent connections. Do not put keys in browser storage, Vite variables,
prompts, screenshots or Git. Environment variables take precedence over dotenv settings.

```powershell
.\.venv\Scripts\python.exe scripts/run_web_demo.py --port 8772
```

Open `http://127.0.0.1:8772`. The helper builds the frontend and serves the API/page
together. Keep one backend running; no reload/multiple workers during jobs. The
helper default remains 8765; the explicit option avoids the previously observed
port conflict. Identify an occupied port before stopping any process.

## Update an existing checkout

Finish active work and stop only this app's backend, then inspect Git status before
updating. If tracked changes prevent the update, preserve them rather than resetting.

```powershell
git status --short --branch
git fetch origin
git switch main
git pull --ff-only
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
npm.cmd --prefix web ci
.\.venv\Scripts\python.exe scripts/run_web_demo.py --port 8772
```

Keep ignored settings, saved data, accepted chair files and the external Unreal
project. No ARC runtime rebuild or new model job is needed for a source/doc update.

## Choose a connection check

- **Connections -> Test ARC connection:** a small authenticated hosted planner request.
- **Asset library -> Check ARC connection:** SSH worker/runtime-marker check; it does
  not run GPU inference or prove the new SDXL stage.
- **Editor connected:** requires manually loading the local bridge once in the open
  Unreal editor. It does not authenticate the hosted planner or ARC SSH.

A configured badge is not proof that a check passed. Current chair room limits are
bounded rectangular rooms, one exit and reviewed-chair placement; inspect model
interpretation and layout geometry. Unknown furniture is not silently substituted.

## Persistence and recovery

Jobs, plans, artifacts, assets and recordings live under ignored `logs/studio/`.
Room planner restart/failure does not silently spend another hosted request.
Asset dispatch uncertainty uses **Reconnect / resume same job**, not another submit.
Trash is recoverable and retains files; it does not delete external Unreal maps.

This app is unauthenticated and single-user. Bind to loopback, use VPN where required,
and keep sensitive trainee/medical/operational data out. See
[room pipeline](studio-pipeline-runbook.md), [asset setup](asset-automation-runbook.md),
[security](security/README.md) and [CI](development/ci.md).
