# Read a sample debug panel in Unreal

This is the first Unreal step.

The goal is boring on purpose:

> Unreal shows backend-owned state as text.

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

Start with the text bridge:

```text
Data/hallway_debug_panel.sample.txt
```

That file is generated from backend-shaped JSON. It lets Unreal prove the display path before it has to parse JSON.

Refresh it from the repo root with:

```powershell
python scripts/write_unreal_debug_text.py
```

The source JSON files are:

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

And you can write the exact text file Unreal should show:

```powershell
python scripts/write_unreal_debug_text.py --stdout
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
6. Load `Data/hallway_debug_panel.sample.txt`.
7. Put that file content into one readable string.
8. Set `DebugText`.
9. Add the widget to the viewport on Begin Play.

The first version does not need a beautiful UI.

If it looks like a console panel, that is fine.

## What not to parse yet

Do not try to support every future field.

For the text bridge, Unreal does not need to parse these fields yet. It only displays the finished text.

When Unreal is ready to parse JSON directly, only parse:

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
- it reads the checked-in text bridge file
- it shows session/scenario/phase/status text
- it lists warnings and errors
- it lists object rows
- it marks `attention` rows clearly
- it does not change scenario state
- it does not contain local validation rules
- it does not load assets or simulate physics

## After this works

Only after the text bridge works, the next step is direct JSON parsing:

```text
display-state JSON
  -> Unreal parser
  -> same text panel
```

After that works, the next step is live backend connection:

```text
backend WebSocket
  -> scenario_state_update
  -> simplified display state
  -> same text panel
```

That live step comes later.
