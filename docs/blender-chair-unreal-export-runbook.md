# Reviewed chair: Unreal export checkpoint — 2026-10-18

Andy inspected `chair-collision-complete.blend` and said it looks good. The next authorized step is export and Unreal import preparation, retaining automation rather than per-object manual edits.

## Prepared deliverable

`chair-unreal-export.zip` contains `unreal-chair-export/` with:

- `SM_Chair_Demo.fbx`: one render mesh and 19 matching `UCX_SM_Chair_Demo_00`–`_18` collision meshes only.
- `textures/T_Chair_BaseColor.png`, `T_Chair_Roughness.png`, `T_Chair_Metallic.png` (1024 x 1024).
- `material-plan.json`: two used slots, explicit texture/color-space/channel connections and cut-face scalar values.
- `blender-collision-report.json`, `export-manifest.json`, `README.md` with hashes, provenance and import checkpoint.

The file is ready for an Unreal import attempt. It has NOT been imported into Unreal or run through Chaos. Confirm Andy's installed Unreal version (or whether it is installed) before choosing exact menus or an Editor Python automation script. Prefer a separate POC project/content folder when preparing the demo.

## Reproduce with one Blender script

On `chair-collision-complete.blend`, Object Mode: Scripting > Text > Open > `scripts/blender/export_hunyuan_chair_unreal.py` > Text > Run Script. It creates a new `unreal-chair-export` folder beside the saved `.blend`, refusing existing output folders. It does not save the Blender file. The already-produced package is an alternative; Andy need not run the exporter again.

Exporter uses a temporary scene with copies, preserves the original scene and selection, exports only the 20 intended meshes, removes an unused third material slot from the export copy, restores face assignments explicitly, and writes separate roughness (packed G) and metallic (packed B) PNGs as linear data. Source textures, mesh, UVs and manual collision backups are untouched. Temporary material names are M_Chair_Wood and M_Chair_CutFaces. No automatic FBX texture/material conversion is assumed.

## Verification completed

Official bpy 5.1.2. Exporter succeeds; FBX reports version 7400. Export/import roundtrip in a fresh scene preserves 20 meshes, 19 collision pieces, render 72,664 triangles, active UVs, two used material slots and their triangle assignments (69,421 wood / 3,243 cut-face triangles). World bounds match source within 1e-5 m, with Z from 0 to .999956965 m. Roughness and metallic PNGs reloaded as Non-Color match original packed channels exactly. Source object names, geometry, transforms, hide flags, UVs, packed pixels, scene object set, and active scene remain unchanged; existing-output guard rejects overwrite. Python compile and Ruff pass.

Blender roundtrip is a useful export check, not proof of Unreal unit conversion or collision cooking. Verify approximately 100 cm height at import scale 1, Z-up orientation, floor pivot, 19 simple hulls, material slots and texture appearance inside Unreal before simulation.

## Unreal import intent (version-specific instructions pending)

Import as one static mesh using named UCX collision, automatic collision generation off, one convex hull per UCX on, scale 1 with scene/units conversion. Exclude auto-created materials/textures; connect the supplied maps explicitly. Use simple collision for dynamic physics, never Complex As Simple. Actor scale remains uniform (1,1,1). Inspect hulls and dimensions in the Static Mesh Editor. Then create a separate visual demo scene with floor, lighting and drop/tip tests; mass/friction remain recorded demo assumptions until calibrated. No fracture or load-bearing validity is implied.

Official references: https://docs.blender.org/api/5.1/bpy.ops.export_scene.html and https://dev.epicgames.com/documentation/unreal-engine/fbx-static-mesh-pipeline-in-unreal-engine .
