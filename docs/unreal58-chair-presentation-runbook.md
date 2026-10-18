# Chair presentation and recording — Unreal 5.8

## Starting point

On October 18, Andy executed the original scene setup in Unreal and reported that both raised chairs fell and settled on the floor within one or two seconds. Screenshots show the textured chairs in the editor and resting during simulation. This establishes an observed basic gravity/contact/settling demonstration, not calibrated physical accuracy or a full emergency scenario.

The next script creates a separate presentation level from the original scene's existing chair, floor material, and physical material. It does not reimport assets, generate models, modify shared materials/meshes, or save over the original level. New level folders are unique. A failed partial presentation can remain in its new folder; return to the original map to retry.

## One execution

1. Extract `chair-unreal58-presentation.zip` anywhere convenient. Keep both Python files together. No FBX or texture files need copying into this folder.
2. In the existing EmergencyChairPOC project, press Esc to stop simulation. Open the original `L_ChairVisualDemo` if another level is open. Press Ctrl+S.
3. Choose File > Execute Python Script and select **prepare_unreal58_chair_presentation.py**. The other Python file is a bundled helper; do not execute it separately.
4. Wait for `CHAIR PRESENTATION READY` in Output Log. The new level is saved under `/Game/EmergencyPOC/ChairPresentation_<unique id>/Maps/L_ChairVisualDemo`. It has the same short name as the original but a separate folder; use the full path in the report to distinguish them.
5. Inspect the complete camera view once. Expect a title, pipeline subtitle, three fixed captions, and a small note that the physics values are demo assumptions. Press G if icons are visible. If the camera view is lost, select Demo camera in the Outliner and use Pilot.

The camera faces the chairs more directly. Reference stays at Z=0; upright starts with its floor pivot at Z=100 cm, tilted starts at Z=120 cm and 30-degree roll. All chairs have 180-degree yaw relative to the first demo. Both moving chairs keep the original demo settings: assumed 5 kg, friction .55, restitution .05, with gravity. These height/angle choices are test conditions, not real measurements. The simulation uses the project's existing time settings; the script does not slow it down or introduce a scripted animation.

## Record a short clip

This is a repeatable manual capture, not an automatic Sequencer/Movie Render Queue recording. No extra Unreal plugins are required beyond the already enabled Python plugin.

1. Stop simulation, leave the camera view visible, and ensure icons/selection outlines are hidden. If desired maximize the viewport using its menu's Immersive Mode.
2. With Unreal active, press Windows+Alt+R to start Xbox Game Bar recording. If Game Bar is disabled/unavailable, use an existing screen recorder or Windows Snipping Tool's video capture instead.
3. Leave the initial raised-chair view visible for about three seconds.
4. Press Alt+S to simulate. Watch for eight seconds: falls, contact, then settling. Avoid moving the camera during the clip.
5. Press Windows+Alt+R again to stop recording, then Esc to end simulation. Game Bar normally puts the clip in Videos/Captures. Check the resulting video before sharing it.
6. Send the short clip for review. No further per-object screenshots are needed. Do not use Keep Simulation Changes: Esc should restore the starting transforms for the next take.

Suggested spoken explanation: “This chair was generated and textured with Hunyuan on VT ARC, repaired and scaled in Blender, and imported into Unreal with simple convex collision. The moving copies respond to gravity and settle on the floor. This demonstrates the asset pipeline; the physical properties are provisional.”

## If setup fails

Return the first red Python error, or the newest `chair-presentation-*.json` under the project's Saved/EmergencyPOC folder. If it says save first, Ctrl+S then rerun. If it says stop simulation, Esc then rerun. If already on a presentation map, reuse it rather than rerunning; to create a fresh copy open the original map first.

## Validation boundary

Python compilation/lint and bundled-helper hash/missing/tampered-file checks run outside Unreal. The original scene has now been run and observed on Andy's PC. The new presentation layout, label rendering, and capture must still be reviewed there; no Unreal runtime is available in the authoring environment.

Official references: [Epic TextRenderComponent](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/TextRenderComponent), [Epic LevelEditorSubsystem](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/LevelEditorSubsystem), [Microsoft Game Bar recording](https://support.microsoft.com/en-us/accessibility/windows/use-a-screen-reader-to-record-your-screen-with-xbox-game-bar).
