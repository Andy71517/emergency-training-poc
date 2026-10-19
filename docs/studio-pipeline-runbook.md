# FIELDWORK pipeline handoff — 2026-10-18

Resume here for the frontend/local worker batch on `codex/arc-scenario-workspace`, draft PR #7. Earlier ARC evidence remains in `arc-handoff-2026-10-18.md` and `arc-handoff-2026-09-28.md`.

## Windows update

Stop uvicorn with Ctrl+C. From the repository root:

```powershell
git pull --ff-only
npm --prefix web ci
npm --prefix web run build
notepad backend\.env
```

Keep the existing key and model. Add these paths, using your actual installation and prepared chair locations:

```dotenv
BLENDER_EXECUTABLE=C:/Program Files/Blender Foundation/Blender 5.1/blender.exe
CHAIR_BLEND=C:/your-assets/chair-collision-complete.blend
```

Use the completed chair with `SM_Chair_Demo` and 19 `UCX_SM_Chair_Demo_*` pieces, not the original GLB. Copy as path can help; enclosing quotes are accepted. Do not overwrite your existing `.env` with the template. Values are read again per request, so path changes do not require a restart.

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765
```

Open http://127.0.0.1:8765. In Connections, **Test ARC connection** makes a small authenticated model request. A configured key alone is not connectivity evidence. Use VT VPN if required. The screenshot received on October 18 showed a failed planning attempt with a generic error; its exact cause is unknown. Transport/timeouts, HTTP responses, plan errors and unexpected response formats now have separate messages. Old jobs retain old messages; test and explicitly retry to get current diagnostics.

## Connect Unreal once per editor session

1. Backend and Unreal must use the same computer and checkout. The bridge polls `logs/studio/engine`; no public listener or new plugin is installed.
2. Open Unreal 5.8 and your saved original/presentation chair demo with its **Display chair** actor. Existing Python/editor scripting support must be enabled.
3. Save work and stop any active simulation.
4. **Tools → Execute Python Script → unreal/scripts/studio_bridge.py** in this checkout.
5. Keep Unreal open. Connections should show **Editor connected** within a few seconds. Use one editor instance per checkout.

The first assembly validates/binds the chair's 19 hulls, 100 cm height, floor pivot and two material slots. Later batches reuse the mesh binding until Unreal restarts. Reloading the bridge while it has a task is refused. Backend restarts mark interrupted work and cancel unclaimed commands; they do not establish completion of claimed editor work.

## Controls and actual work

| Control | Work and output |
| --- | --- |
| Generate batch | Real ARC plan request, bounded validation, seeded room specifications and SVGs; no substitute fixture on failure |
| Edit brief / Retry | Revise the composer or explicitly create another model request; old job remains |
| Rebuild with seed | New job from saved validated plan; no LLM request |
| Whole batch | Download room JSON/SVG, manifest and portable Blender scripts; chair binary excluded |
| Build in Blender | Background Blender 5.1 assembles prepared chairs into a new rooms.blend, renders overview PNG and saves report; source asset untouched |
| Assemble in Unreal | Open editor bridge builds one new map per scene and returns matching assembly evidence |
| Run Chaos batch | Load each generated map, simulate ten seconds, read chair positions from its game world, stop simulation and return observations |
| Unreal handoff ZIP | Alternative: extract and execute assemble_unreal58_rooms.py manually in the original chair demo |
| Import assembly report | Check job ID, room hashes and map entries from Saved/EmergencyPOC/room-setup-*.json; not proof of simulation |

Inspect Blender previews/files and Unreal maps. The room count supports 1–30. Blender uses CPU rendering and the existing serial local worker, with a 30-minute timeout; large batches take longer. A separate scene per room plus an overview is saved. Scene data is reused across both applications.

Chaos reports show editor-reported initial/final positions and endpoint displacement. They do not measure collision contacts or verify evacuation behavior/calibrated physics. Floor-level chairs may legitimately remain still; no extra impulse is applied. Chair height, mass and material parameters are demo assumptions. The browser displays Blender renders and engine reports; Unreal video is not streamed.

The bridge only accepts fixed assemble/simulate actions. Model text is never executed. Keys stay backend-only and are stripped from Blender child environments; raw process/network output is not persisted by these workers. Env and worker files remain local under ignored logs/config paths.

API references: [LevelEditorSubsystem](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/LevelEditorSubsystem), [UnrealEditorSubsystem](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/UnrealEditorSubsystem). Uses documented editor_play_simulate, editor_request_end_play and get_game_world calls.

## Validation and practical limits

- Backend regression suite: 91 passing tests on a snapshot of tracked GitHub sources plus this batch.
- Production frontend build and ESLint; targeted Python lint and compile checks.
- Browser flow with explicit offline fixture planner: generation, focus alignment, stage navigation, Connections, Unreal ZIP download, saved-plan replay, desktop/mobile layout and no page errors.
- Actual Blender 5.1.2 Python runtime ran assembly and rendering with the accepted three-room plan and completed chair; new blend/report/preview produced and preview inspected. The Windows executable invocation still needs the first user-side run.
- Tests cover replay without another model call, ZIP/report hash binding, rejected foreign origins, sanitized failures, editor command/result flow and restricted artifacts. A fake editor exercises bridge simulation-start/game-world-sampling/stop. This does not claim real Unreal execution.
- Live ARC frontend generation and actual Unreal 5.8 bridge execution remain user-side checks; no credentials or Unreal installation are available in the build environment.

## Next actions

1. Update, add Blender paths, restart backend and test ARC. Share only sanitized errors if it fails.
2. Generate three layouts, build in Blender and inspect the returned render/file.
3. Load the bridge in the chair demo, Assemble in Unreal and inspect new maps.
4. Run Chaos batch; watch Unreal cycle maps, then inspect/download its observations in the frontend.
5. Add camera/video evidence and quantitative physics checks after the Windows bridge works.
6. Add ARC job submission for new asset requests and reviewed asset registration. New Hunyuan/TRELLIS generation and general mesh repair are not part of this local reuse worker. TRELLIS/DINOv3 remains paused pending access. Agents, smoke and arbitrary asset types remain later work.
