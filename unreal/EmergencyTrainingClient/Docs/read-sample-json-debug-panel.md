# Read a sample JSON debug panel in Unreal

This is the first Unreal step.

The goal is boring on purpose:

> Unreal reads a checked-in JSON file and shows the backend-owned state as text.

Do not build a real scene yet.

Do not add gameplay logic, physics, generated assets, sensing, projection mapping, or local validation.

## What this proves

This proves that Unreal can act as a display client.

It does not prove the final simulator yet.

The backend still owns:

- scenario state
- validation results
- warning/error logic
- final outcome
- replay and review

Unreal only shows the state it receives.

## Files to start with

Use one of these local sample files:

```text
Data/display_state.sample.json
Data/warning_display_state.sample.json
Data/hallway_display_state.sample.json
```

The hallway sample is useful because it shows the second deterministic scenario:

```text
blocked_exit_hallway_v0
```

You can preview the same display from Python before touching Unreal:

```powershell
python scripts/preview_unreal_display.py --display-state unreal/EmergencyTrainingClient/Data/hallway_display_state.sample.json
```

## Suggested Unreal setup

Create a blank Unreal project first.

Recommended settings:

- Template: Blank
- Type: Blueprint
- Starter Content: off
- Target: Desktop
- Name: `EmergencyTrainingClient`

For the first pass, it is okay to create this outside the repo. That keeps Unreal-generated folders from making Git messy while we test the idea.

## First debug panel shape

The panel can be plain text.

Show:

```text
Session: demo-hallway
Scenario: blocked_exit_hallway_v0
Phase: scene_assessed
Validation: warning
Status: scene_assessed / warning / 1 warning(s)

Warnings:
- environment_not_monitored: ...

Objects:
- [normal] Collapsed bookshelf: moved aside
- [normal] Hallway exit door: open
- [normal] Hallway smoke/haze cue: checked
- [attention] Ongoing hallway monitor: unchecked
```

If `alert_level` is `attention`, make the row stand out.

It can be amber text, a prefix like `[attention]`, or both.

## Blueprint-friendly approach

One simple way to build this:

1. Create a blank level.
2. Create a Widget Blueprint named `WBP_DebugDisplay`.
3. Add a large Text widget.
4. Add a variable named `DebugText`.
5. Bind the Text widget to `DebugText`.
6. Load one sample JSON file.
7. Convert the important fields into one readable string.
8. Set `DebugText`.
9. Add the widget to the viewport on Begin Play.

The first version does not need a beautiful UI.

If it looks like a console panel, that is fine.

## What not to parse yet

Do not try to support every future field.

Only parse:

- `session_id`
- `scenario_id`
- `phase`
- `validation_status`
- `status_line`
- `warnings`
- `errors`
- `objects[].label`
- `objects[].display`
- `objects[].blocks_path`
- `objects[].alert_level`

That is enough for the first proof.

## Acceptance checklist

The Unreal debug display is good enough when:

- it opens without needing the backend
- it reads one checked-in sample JSON file
- it shows session/scenario/phase/status text
- it lists warnings and errors
- it lists object rows
- it marks `attention` rows clearly
- it does not change scenario state
- it does not contain local validation rules
- it does not load assets or simulate physics

## After this works

Only after the sample JSON display works, the next step is live backend connection:

```text
backend WebSocket
  -> scenario_state_update
  -> simplified display state
  -> same text panel
```

That live step comes later.
