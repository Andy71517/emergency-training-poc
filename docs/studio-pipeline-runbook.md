# Room studio and local workers

Current guide for `main`. [Current status](current-status.md) records runtime
evidence. The user confirmed hosted room planning, Blender room assembly, Unreal
assembly and Chaos batches. Furniture automation has a separate
[setup/runbook](asset-automation-runbook.md); existing room workers still use the
accepted wooden chair.

## Install and configure

Follow [workspace setup](arc-workspace-runbook.md). Preserve `backend/.env` and set
the hosted planner key/model, actual `BLENDER_EXECUTABLE` and `CHAIR_BLEND` paths.
Use the accepted collision-complete chair with `SM_Chair_Demo` and 19
`UCX_SM_Chair_Demo_*` pieces, floor pivot and the expected height/material setup.
Do not replace it with the raw GLB or a new unreviewed design.

```powershell
.\.venv\Scripts\python.exe scripts/run_web_demo.py --port 8772
```

Open `http://127.0.0.1:8772`. Use one local process, without reload/multiple workers
during active work. **Connections -> Test ARC connection** makes a small hosted
model request. Configuration alone does not prove access. Use VT VPN when required.

## Connect Unreal once per editor session

1. Backend/editor use the same workstation and checkout. Save work and stop simulation.
2. Open the existing Unreal 5.8 chair/presentation project with its Display chair actor.
3. Enable its existing Python/editor scripting support.
4. Execute `unreal/scripts/studio_bridge.py` through **Tools -> Execute Python Script**.
5. Wait for **Editor connected** in Connections. Keep one editor instance per checkout.

The bridge polls `logs/studio/engine`; it adds no public listener. It accepts fixed
assemble/simulate/record actions. First assembly validates/reuses the reviewed chair
binding; subsequent maps reuse it until editor restart. Reload during a task is
refused. Restarting the backend cannot prove a claimed editor command completed.

## Controls and outputs

| Control | Actual work |
| --- | --- |
| Generate batch | Hosted plan request, bounded validation, seeded chair room JSON/SVGs |
| Existing match / fresh plan | Exact-input reuse; explicit choice before another model request |
| Rebuild with seed | New layouts from a saved validated plan; no new LLM request |
| Whole batch | Room files, manifest and portable Blender scripts; chair binary excluded |
| Build in Blender | Background local room assembly, new `.blend`, overview PNG and report; source chair retained |
| Assemble in Unreal | One map per scene through the open editor bridge, matching assembly evidence |
| Run Chaos batch | Ten-second simulation per map and reported initial/final chair positions |
| Record movement demo | Fixed capture workflow, saved frames/observations and MP4 encoding; first live acceptance pending |
| Unreal handoff ZIP | Manual alternative to the editor bridge |
| Import assembly report | Validates job/room hashes/map entries; not simulation evidence |
| Delete / Trash / Restore | Recoverable batch history; files and external maps remain |

Room count supports 1-30. Layouts use the reviewed-chair footprint, bounded room
dimensions, aisle and exit assumptions. Geometric overlap is not proof of an
impassable exit or evacuation validity. Review plan assumptions and every layout.

Blender uses CPU rendering and a serial local worker with a bounded timeout. Save
files/previews and engine reports are distinct outputs. Ground-level chairs can
remain still in Chaos; endpoint displacement is not contact or calibrated physics
evidence. No extra impulse is added by the ordinary Chaos batch. The recording demo
is a separately labeled input, not a real-world force measurement.

## Errors, restart and privacy

Old jobs retain old diagnostics; explicitly retry when testing a fix. Unexpected
model/transport output must fail instead of becoming a fixture result. Windows ARC
HTTPS uses verified native truststore validation; do not disable TLS checking.
`arc/scripts/check_arc_network.py` can test DNS/TCP/TLS without a model key. Its
401/403 response establishes valid HTTPS, not authorization.

Saved local work persists under ignored `logs/studio/`. Worker credentials stay
backend-owned and are stripped from Blender children. Inspect native logs locally
and sanitize them before sharing. Model text is data, never executable worker code.

## Next acceptance work

The description-based furniture lane now uses Blender MCP for cleanup and collisions,
but new designs do not enter room assembly automatically. Review the first actual
couch and validate its generic Unreal import before coordinating mixed-asset planner,
footprint and Blender/Unreal bindings. Verify actual recording frames/MP4 separately.
See [asset guide](asset-automation-runbook.md), [playback](visual-playback-runbook.md),
[history](batch-history-and-assets.md) and [current evidence](current-status.md).
