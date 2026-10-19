# Unreal 5.8 chair demo setup — prepared, engine run pending

Andy confirmed Unreal Engine **5.8**. He requested scripts instead of repetitive object edits. This setup imports the reviewed Blender export and creates a separate lit demonstration map. It must run in Andy's actual Unreal Editor; no Unreal runtime is available in the assistant environment.

## Beginner execution

1. Download and extract `chair-unreal58-demo-setup.zip` with Windows Extract All. Keep `setup_unreal58_chair_demo.py`, `SM_Chair_Demo.fbx`, the JSON files, and `textures/` together inside `unreal-chair-export/`.
2. Open Unreal 5.8 and create a **Games > Blank > Blueprint** project named `EmergencyChairPOC` (or open a separate POC project). No C++ build is needed.
3. Edit > Plugins: search **Python Editor Script Plugin**, enable it, and restart the editor when prompted. The script uses core editor subsystems rather than the deprecated Editor Scripting Utilities wrappers.
4. Save the current level with Ctrl+S. If asked for a name, use `L_StartingPoint`. This avoids losing unsaved work when the script switches to the new demo map.
5. File > Execute Python Script: select `setup_unreal58_chair_demo.py` from the extracted folder. Do not run it in Blender or in a normal Windows Python terminal.
6. Allow import/material compilation to finish. On success, a new level with three chairs, a floor, three area lights and a camera opens. Actor labels in the Outliner distinguish `Display chair`, `Upright drop`, and `Tilted drop`.
7. Inspect the scene once. To test physics, press **Alt+S** (Simulate), watch the two elevated chairs fall, then **Esc** to stop. The display chair stays fixed. Setup itself does not start or record simulation.
8. Return one overall screenshot and the observed behavior. If setup fails, open Window > Developer Tools > Output Log (or search Output Log), copy the red Python error, or send the generated report from the project's `Saved/EmergencyPOC/` directory. Stop at the first failure; do not manually patch assets or assume success.

## Intended behavior and safeguards

- Verifies the original FBX/texture/material-plan hashes before importing.
- Requires a 5.8.x engine, stopped Play/Simulate session and no dirty map packages.
- Uses a fresh `/Game/EmergencyPOC/ChairDemo_<timestamp>_<suffix>` content folder and new map on each run; no existing assets are replaced or deleted. A failed run may leave partial assets under its own new folder, documented in the error report.
- Temporarily disables only Interchange's FBX feature flag to use explicit legacy FbxFactory options (UCX names, one hull per piece, no auto collision/material import), then restores its previous value in a finally block. Does not disable plugins or edit project configuration files.
- Requires exactly 19 imported convex hulls, height within 1 cm of 99.9957 cm, and floor pivot within .5 cm of Z=0 before building the level. No silent unit correction or auto-generated substitute collision.
- Imports the three textures; sets base color sRGB, roughness/metallic linear Masks; creates two explicit chair materials and a neutral floor material. Assigns chair slots by imported material names, rejecting unexpected layouts.
- Uses simple-and-complex collision with the 19 simple hulls for physics. Three chair actors share the mesh: fixed display, upright drop from 65 cm, tilted drop from 85 cm with 30-degree roll.
- Sets the two dynamic chairs to an **assumed 5 kg**, friction **.55**, restitution **.05**, linear damping **.05**, angular damping **.1**. These are demo settings, not calibrated chair properties. Gravity uses the project's settings. The floor is a 14 m square, 10 cm thick cube, with its top at Z=0.
- Creates a JSON report on success or failure in `Saved/EmergencyPOC/`. A success report establishes setup checks only, never successful simulation, physical realism, or structural validity. No destruction/fracture behavior is created.

## Validation boundary

Completed here: Python 3.11-compatible parsing/compile, Ruff, original package hash verification, altered/missing texture rejection, import of the script without Unreal or side effects, and bundle ZIP integrity. Existing FBX roundtrip and collider checks are documented in `docs/blender-chair-unreal-export-runbook.md` and `docs/blender-chair-collision-runbook.md`.

**Not executed here:** Unreal asset imports, engine property calls, material shader compilation, level creation, collision cooking, or Chaos simulation. The first engine run on Andy's PC is the integration test. API/property issues must be fixed from the returned error and report; do not describe this as engine-tested.

## Official references checked

- Python plugin and File > Execute Python Script: https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python
- FBX collision names/options: https://dev.epicgames.com/documentation/en-us/unreal-engine/fbx-static-mesh-pipeline-in-unreal-engine
- Interchange FBX feature flag: https://dev.epicgames.com/documentation/en-us/unreal-engine/importing-assets-using-interchange-in-unreal-engine
- LevelEditorSubsystem new_level explicitly closes current level without saving: https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/LevelEditorSubsystem
- MaterialEditingLibrary connections: https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MaterialEditingLibrary

## Resume after first run

Inspect screenshot/report and verify size, 19 hulls, materials and camera framing. Observe/record upright and tilted drops. Adjust fit/contact/material settings only when results justify changes. Then capture a short visual clip for Dr. Cameron with accurate provenance and limitations. Keep the paused TRELLIS/DINOv3 lane available; this demo uses the successfully generated Hunyuan asset.
