# Blender chair repair preview — 2026-10-18

Approved Blender batch; this is its backrest repair checkpoint. Collision and Unreal export remain pending.

## Input and scope

Use the uploaded `chair-cleanup.blend` from Hunyuan shape job 8052814 and paint job 8053348. Blender 5.1.2, mesh `chair-textured.obj`, 49,933 vertices / 80,000 triangles, dimensions approximately 0.542 x 0.633 x 1.000 m. Height is an assumed demo size, not a verified real-world measurement. Both textures are packed.

Solid and Edit Mode inspection confirmed fused surfaces between backrest slats. The script is specific to this exact uploaded mesh and placement; it rejects other counts/bounds. It is not a general AI mesh repair utility.

## Run in Blender

1. Open your saved `chair-cleanup.blend` and return to Object Mode.
2. Download `scripts/blender/repair_hunyuan_chair_backrest.py` from this branch.
3. Click the Scripting workspace. In the Text Editor choose Text > Open and select the downloaded Python file.
4. Choose Text > Run Script. No add-on installation is required.
5. Return to Layout and choose Material Preview. The original is hidden; `Chair_Repaired_Preview` is selected. Inspect front, back and sides.
6. Use Save As to save a separate `chair-repaired-preview.blend`. The script itself never saves files.

To abandon the preview, reopen the saved input without saving changes. To compare within the scene, hide the preview and unhide the source in the Outliner. Do not show both at once: they overlap. Cutters are hidden viewport/render objects referenced by five live Boolean modifiers. Do not delete them. Do not apply the modifiers until the visual review is complete. A second script execution is deliberately rejected.

## Changes

- Duplicate object and mesh, weld coincident positions on copy while retaining per-corner UVs.
- Lift copied geometry by 0.0265686512 m so its lowest point is exactly Z=0, keeping object origin at world zero. Earlier manual median-based centering did not put the bounding-box bottom on the floor.
- Five exact Boolean differences reopen the gaps while retaining rails/posts and slats. Newly cut faces receive an approximate solid brown nonmetallic material.
- Copy the albedo/material and tint 94,203 pale neutral pixels brown. This removes generated background-colored remnants; it is approximate paint correction, not recovered wood grain. Original images and material remain unchanged. Roughness/metallic maps are retained; gloss still needs review.
- Preserve and hide the source. Add provenance/scale notes as custom properties.

## Validation on actual uploaded file

Executed using official `bpy==5.1.2` Linux Python package. Closed welded input: 39,992 vertices / 80,000 faces. Evaluated repair: 36,318 vertices / 67,842 polygons, 72,664 triangles, zero nonmanifold edges, 20 cut-surface polygons. Finite coordinates; lowest evaluated point within 1e-5 m of zero. Source vertex coordinates, UV values, and original albedo pixel digest unchanged. Repeated execution rejected. Saved/reopened temporary test copy and rendered front and rear in Cycles CPU. No uploaded file was overwritten.

Visual result: five open gaps, recognizable original textured chair. Remaining rough slat ends, texture/shading differences and generated geometry are visible. This is a demo repair, not production retopology, physical validation, or a finished collision asset. Modifier operations are reversible; weld/tint exist on copies. Full self-intersection and stability validation remain pending.

## Next

Review Andy's local preview, then refine materials if needed, verify foot contact, build simple convex collision pieces, export only evaluated render mesh plus collision assets, and verify import/scale/materials in Unreal before Chaos drop/tip tests. Mass and friction must be recorded as demo assumptions. Do not use the visual mesh directly as dynamic triangle-mesh collision.
