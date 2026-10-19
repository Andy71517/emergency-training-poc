# Blender-reviewed rooms into Unreal 5.8

Andy accepted the three-room Blender preview on October18. This batch completes assembly in Unreal before starting frontend work. The later frontend should be clean/minimal/futuristic; do not replace current room tasks with a new UI implementation.

## Run once

1. Extract three-rooms-unreal58-setup.zip anywhere. Keep the Python script, room-package.json and three room_NNN.json files together. No new model download, ARC job, Blender export or texture copying is needed.
2. Open EmergencyChairPOC in Unreal5.8. Open the original chair demo or corrected chair presentation, with its Display chair actor. The script binds that actor's already imported static mesh and materials. Stop simulation with Esc; save current level with Ctrl+S.
3. File > Execute Python Script > assemble_unreal58_rooms.py.
4. Wait for ROOM SETUP COMPLETE in Output Log. Three maps are saved under Content/EmergencyPOC/Rooms_<unique id>/Maps. The last map, room003_obstructed, remains open and the script attempts to pilot Room review camera.
5. Click inside the viewport and press G to hide editor icons. Inspect the complete room: 12 chairs, green aisle guide, rear doorway and obstruction marker in room003. The front wall is invisible for the camera view, but retains collision. There is no ceiling or simulated door leaf.
6. In Content Drawer open the other two maps in the same Maps folder to inspect their clear aisles. If not in camera view, select Room review camera in Outliner and Pilot it. No manual furniture movement is required.
7. Press Alt+S to run Chaos, observe for five seconds, Esc to stop. Chairs begin on the floor at exactly the reviewed positions; large motion is not expected. Report any falling through floor, inversion, continual jitter or unexpected displacement. Do not Keep Simulation Changes.

Return one overall screenshot from room003 and observations. If setup fails, share the first red Python error or newest Saved/EmergencyPOC/room-setup-*.json. Partial new materials/maps can remain after failure; baseline chair demo is not overwritten. Retry from the original chair demo, not a room map, because binding requires Display chair.

## What this actually does

The same hash-verified ARC spatial JSON that was assembled/reviewed in Blender drives Unreal assembly. Room structure is rebuilt from those dimensions using Engine Cube instances; the reviewed chair already in Unreal is instanced. This is shared-specification assembly, not importing a monolithic Blender room FBX. The package records the accepted Blender artifact hash and original ARC room hashes. The engine binding validates mesh material count, 19convex hulls, approximately100cm height and floor pivot; it is not a cryptographic comparison of Unreal's cooked asset to Blender geometry.

Walls/floor use BlockAll, real doorway gaps and lintel. All three maps retain invisible front-wall collision for a complete perimeter except the exit. Green/red guides and captions have no collision. Chair transforms are written to mesh components explicitly and read back in centimetres with upright checks. Metres multiply by100 once; Engine Cube dimensions100cm mean metre dimensions numerically equal its scale factors.

For this engine demonstration the source draft's static_review designation is overridden explicitly: all12chairs are enabled as movable PhysicsActor rigid bodies at their existing floor positions with assumed5kg, friction.55, restitution.05. The report records this override. Their real physical properties remain uncalibrated; the original spatial JSON is untouched. No simulation runs automatically and setup success does not prove physical behavior.

Three layout scenes, not evacuation-agent simulations. A chair intersecting the designated aisle is not proof that the exit is impassable. No smoke, fire, navigation agent, scoring, backend integration or frontend is added here.

## Verification boundary

Python compile/lint, pure package hash/count/axis checks, altered-room rejection, metre conversion checks and archive integrity run before delivery. Existing chair setup and component repair have user runtime evidence. This NEW room assembler has not run in Unreal here; first execution on Andy's PC verifies engine API calls, map creation, rendering and physics. Do not call this completed engine integration until returned observations are reviewed.
