# FIELDWORK: Emergency Training Simulator POC

FIELDWORK combines a local scenario studio, ARC-assisted room planning, generated
furniture preparation, and Blender/Unreal review tools. A separate deterministic
training-session demo provides ordered actions, rule checks, logs, replay, and review.

The long-term goal is natural language to complete editable environments and an
adaptive emergency-training experience. The current room workflow reuses one reviewed
wooden chair. The new chair/couch asset workflow prepares individual designs; mixed
furniture rooms are not connected yet.

## Current capabilities

| Workflow | What exists | Evidence and remaining boundary |
| --- | --- | --- |
| Scenario studio | Hosted ARC planner, validated plans, seeded room layouts, SVG previews, saved batches, replay, Trash/Restore | User confirmed live planning and the chair room workflow. Model errors do not silently fall back to fixtures. |
| Furniture generation | Description -> SDXL reference on ARC -> Hunyuan shape/paint -> retrieved model | Implemented SSH/Slurm workflow; first live automated couch run remains blocked on one-time SSH setup and remote checkout update. |
| Blender MCP | Fixed preparation tools, conservative cleanup, convex collision pieces, packed editable `.blend`, preview, FBX/textures/import package | Real Blender 5.1.2/MCP/CoACD preparation passed on a synthetic fixture. This is not evidence of a generated couch. |
| Unreal 5.8 | Chair demo, room assembly, editor bridge, ten-second Chaos batches, recording controls | User confirmed chair/room/Chaos runs. First live recording and generic furniture importer/collision cooking remain unverified. |
| Session baseline | Two deterministic YAML scenarios, WebSocket actions/state, JSONL logs, replay and instructor review | Separate from spatial room generation and physics. These are software fixtures, not validated emergency guidance. |

Start with the [documentation index](docs/README.md) and [current status](docs/current-status.md).
The [October 26 handoff](docs/arc-handoff-2026-10-26.md) records the latest implementation
evidence. Documentation was reconciled on **October 28, 2026**; that date does not
imply a new GPU or Unreal run.

## Install and run locally

Use Python 3.11+ and Node.js 22.13+ within the 22.x line (the CI version). From the repository root in PowerShell:

```powershell
git switch main
git pull --ff-only
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
npm.cmd --prefix web ci
.\.venv\Scripts\python.exe scripts/run_web_demo.py --port 8772
```

Open [http://127.0.0.1:8772](http://127.0.0.1:8772). The helper builds the frontend
and serves the app/API together. On a fresh checkout, copy `backend/.env.example`
to `backend/.env` and configure only the capabilities you need. Preserve an existing
private file. Inspect local changes before switching/updating; do not discard them.
Use one backend process without reload/multiple workers during generation.

Port **8772** is the documented one-port workflow. `run_web_demo.py` still defaults
to **8765** if `--port` is omitted; the Vite development proxy also targets 8765.
If a port is occupied, identify its owner or choose another free port rather than
stopping an unrelated application.

| Private local setting | Purpose |
| --- | --- |
| `ARC_LLM_API_KEY`, `ARC_LLM_MODEL` | Hosted room planner; key stays backend-only |
| `BLENDER_EXECUTABLE` | Installed local Blender executable |
| `CHAIR_BLEND` | Reviewed, collision-complete chair used by existing room workers |
| `ARC_SSH_TARGET`, `ARC_REMOTE_REPO` | Verified SSH host/alias and absolute ARC checkout path for GPU asset jobs |

The hosted planner key does not grant SSH or Slurm access. Never enter passwords,
Duo codes, private keys, or passphrases into the app or chat. Follow the
[asset automation setup guide](docs/asset-automation-runbook.md) for one-time SSH
trust/agent setup and updating the ARC checkout. Open OnDemand remains a setup and
recovery option; routine jobs are designed to use the frontend after SSH works.

## Choose a workflow

- [Room studio and local workers](docs/studio-pipeline-runbook.md): prompt, layouts, Blender rooms, Unreal bridge, Chaos evidence.
- [Description to furniture](docs/asset-automation-runbook.md): automatic reference, ARC job, model retrieval, Blender MCP and Unreal package.
- [Existing reference / manual handoff](docs/furniture-variants-runbook.md): optional PNG and request/result ZIP route.
- [Recorded movement demos](docs/visual-playback-runbook.md): saved frames/clips, with the first live engine recording still to verify.
- [Deterministic session demo](docs/demo-script.md): `python scripts/run_local_demo.py` or `python scripts/run_menu_demo.py --fast`.

For frontend development, run FastAPI on 8765 and Vite on its printed local URL:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765
```

In a second terminal: `npm.cmd --prefix web run dev`. See [web/README.md](web/README.md).

## Checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q backend/tests arc/tests
.\.venv\Scripts\python.exe -m ruff check backend scripts
.\.venv\Scripts\python.exe -m compileall -q backend scripts arc/scripts unreal/scripts docs/presentations/build_pdf.py
.\.venv\Scripts\python.exe scripts/check_json_files.py
npm.cmd --prefix web run lint
npm.cmd --prefix web run build
```

Check ARC `.sh`/`.sbatch` syntax with Bash; on Windows use Git Bash rather than a
WSL launcher receiving Windows paths. The last implementation checkpoint passed
138 backend/ARC tests and GitHub CI. [CI details](docs/development/ci.md) distinguish
offline tests from actual GPU, Blender, and engine execution.

## Repository map

| Folder | Responsibility |
| --- | --- |
| [backend](backend/README.md) | FastAPI, persistent studio/assets/jobs, remote transport, MCP preparation, session engine and review |
| [web](web/README.md) | React studio, asset library, previews, workers, legacy tools and physics lab |
| [arc](arc/README.md) | Configuration, Slurm jobs, pinned generation scripts and portable packages |
| [scripts](scripts/README.md) | Local demos, Blender workers, validation and PDF builders |
| [unreal](unreal/README.md) | Editor scripts/bridge, furniture importer and separate session-client contracts |
| [schemas](schemas/README.md) | Session, scene, physics and pipeline contracts/examples |
| [scenarios](scenarios/README.md), [validation](validation/README.md) | Deterministic toy scenarios and explicit rules |
| [assets](assets/README.md), [artifacts](artifacts/README.md) | Review guidance and ignored local binary outputs |
| [logs](logs/README.md) | Ignored session/physics/studio data, SQLite, worker results and recordings |
| [docs](docs/README.md) | Current guides, architecture, roadmap, reports, presentations and dated history |

## Boundaries and sharing

This remains a local, single-user POC. There is no application login, multi-user
authorization, production deployment, clinical/protocol validation, trainee sensing,
projection mapping, or validated real-time adaptation. Cleanup cannot reconstruct
arbitrary missing/fused parts. Collision proxies and demo physics assumptions need
visual and engine review; they do not establish physical accuracy.

See [security guidance](docs/security/README.md), [scope](docs/poc-scope.md),
[gap map](docs/full-system-gap-map.md), and [full vision](docs/full-project-vision.md).
Markdown is the editable documentation source. Rebuild the report/deck and four-file
submission packet after changing their sources; see [reports](docs/reports/README.md).
