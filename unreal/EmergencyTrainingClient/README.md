# EmergencyTrainingClient Placeholder

This folder is reserved for the future Unreal client.

For now, it contains only a tiny debug-display starter scaffold. It is not a real Unreal project yet.

Do not add a full scene, assets, gameplay logic, physics, sensing, projection mapping, or generated content here yet.

## First Unreal goal

The first Unreal goal should be boring on purpose:

1. Load a debug-display JSON payload.
2. Show it as text.
3. Highlight rows with `alert_level: attention`.
4. Do not change scenario state locally.
5. Do not simulate physics or load meshes.

The backend remains the source of truth.

## Starter files

- `Config/debug-display-panel-fields.json`: the fields the first text panel should render.
- `Docs/debug-display-starter.md`: beginner-friendly notes for the first Unreal implementation pass.
- `Data/display_state.sample.json`: local copy of the clean display payload.
- `Data/warning_display_state.sample.json`: local copy of the warning display payload.

These files are here so the future Unreal work has a tiny target before any scene work starts.
