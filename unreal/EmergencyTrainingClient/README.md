# EmergencyTrainingClient Placeholder

This folder is reserved for the future Unreal client.

For now, it contains only a tiny debug-display starter scaffold. It is not a full Unreal project yet.

Do not add a full scene, assets, gameplay logic, physics, sensing, projection mapping, or generated content here yet.

## First Unreal goal

The first Unreal goal should be boring on purpose:

1. Show a hardcoded debug text panel.
2. Load a generated `.txt` file that was made from backend-shaped JSON.
3. Later, parse the JSON directly.
4. Highlight rows with `alert_level: attention`.
5. Do not change scenario state locally.
6. Do not simulate physics or load meshes.

The backend remains the source of truth.

## Starter files

- `Config/debug-display-panel-fields.json`: the fields the first text panel should render.
- `Docs/debug-display-starter.md`: beginner-friendly notes for the first Unreal implementation pass.
- `Docs/read-sample-json-debug-panel.md`: step-by-step guide for the first Unreal sample-JSON display test.
- `Data/display_state.sample.json`: local copy of the clean display payload.
- `Data/warning_display_state.sample.json`: local copy of the warning display payload.
- `Data/hallway_display_state.sample.json`: local copy of the blocked-exit hallway display payload.
- `Data/hallway_debug_panel.sample.txt`: simple text generated from the hallway JSON sample.

These files are here so the future Unreal work has a tiny target before any scene work starts.

To refresh the sample text from JSON:

```powershell
python scripts/write_unreal_debug_text.py
```
