# First ARC-authored rooms — Blender 5.1.2 review

## Open the prepared result

Extract three-classroom-layouts-blender.zip into its own folder. In Blender 5.1.2 save any current work, then File > Open > three-classroom-layouts.blend. The assembler has already run; no script execution or ARC job is needed.

The active scene POC_00_Overview shows all three rooms as collection instances for comparison. Press Numpad 0 for the camera view if necessary. Use Material Preview to see packed chair textures; the included overview.png is the rendered reference. The Scene selector at the top right switches to POC_room_001, POC_room_002 or POC_room_003 for inspection at actual metre coordinates. Overview rooms have display offsets only; the individual scenes retain exact ARC coordinates.

Check the whole scene once: walls/doorway, chair appearance and sensible size, clear aisles in the first two rooms and one chair overlapping the aisle near the exit in the third. Green strips and red footprint markers are annotations, not simulated surfaces or evidence of evacuation validity. Ceiling omitted and front wall hidden for a cutaway; hidden front wall must be restored for a complete Unreal room collision enclosure. The rear opening is physically empty below its lintel, 1.2m wide x2.1m high. No door leaf or hinge is simulated.

The wooden chairs use the previously reviewed Hunyuan/Blender asset. The walls/floors are procedural meshes constructed from the ARC plan, not newly generated Hunyuan assets. Chair meshes/materials are shared among instances. The 19 convex collider candidates per chair are present but hidden in viewport/render; they are not exported/cooked into Unreal by this batch. Blender rigid-body simulation is not configured.

## Provenance and reconstruction

ARC run directory: /home/anirudhalledula/emergency-training-poc/arc/results/scenario-batches/20261019_003044_818369. Andy supplied plan.json and manifest.json. Replayed room JSON at seeds 20261018/19/20 matches all three original manifest hashes exactly. Source plan/manifest and the verified reconstructed room specifications are bundled under spatial-inputs. request.json was not returned; no new API call or raw model-response audit was performed here. First model plan equals the in-prompt example, so prompt adaptation remains to be demonstrated with a genuinely different request.

The output is a new separate file. The chair source hash is recorded in assembly-report.json and the Blender Text report. Raw uploads/original prepared chair are unchanged. Embedded Text datablocks include each room specification and the assembly report. Source Blender filename: chair-collision-complete.blend, render mesh SM_Chair_Demo and 19 UCX objects. Scale is an assumed demo size, not measured real furniture.

## Reusable assembler

scripts/blender/assemble_scenario_rooms.py exposes assemble(package_dir, chair_blend, output_blend). The prepared download avoids running this yourself. To rebuild a future verified package, run in a separate saved Blender session: it creates output scenes and removes non-POC scenes from the in-memory output session, not from the source file on disk. Never run against unsaved work. It verifies room file hashes and expects the same reviewed source chair. Its input manifest must list every room JSON. Existing output filename is refused.

This assembler is scoped to the generator's current contract: positive-Y centred doorway and fixed reviewed chair asset. It is not a generic importer for arbitrary unvalidated JSON. New room types or assets need contract validation/bindings first.

## Verification completed

Official bpy5.1.2 actual assembly, save/reopen, source hash unchanged, 36 chairs and 684 convex collider instances, embedded texture packing, world positions matching scene JSON within1e-5m and upright orientation. Twenty-seven sample rays through three doorway gaps clear; adjacent side-wall and lintel positive controls hit. Overview rendered and inspected. Python lint/compilation pass. This validates these specific rooms, not all possible future plan geometry or full collision/navigation behavior.

Next: Andy reviews complete Blender result, then assemble the reviewed room specifications in Unreal with source asset binding, metre-to-centimetre conversion checks, complete room collision enclosure and named component-transform readback. Preserve the successful chair physics project. Unreal room assembly and evacuation-agent testing remain pending.
