# Complete Blender collision preview — 2026-10-18

Andy requested one script and one review checkpoint instead of manual collider entry and screenshot loops. Input is his uploaded `chair-collision.blend`: repaired textured `SM_Chair`, live five Boolean modifiers, and manual boxes `UBX_SM_Chair_00` through `_04`. No backrest box was started. Blender 5.1.2.

## Use the prepared file

Open the delivered `chair-collision-complete.blend` in Blender 5.1.2. This is a separate copy with the script already run. Do not run the script again on it. The new collection contains textured `SM_Chair_Demo` and 19 selected wire collision cages. Original objects are preserved and hidden. Inspect the whole chair from front, side, rear and perspective; there is no need to enter individual transforms.

## Or run the script on your own input

1. Save your existing `chair-collision.blend` and return to Object Mode.
2. Download `scripts/blender/complete_hunyuan_chair_collisions.py`.
3. Scripting workspace > Text > Open > select the script > Text > Run Script.
4. Return to Layout. The script switches viewports to Material Preview, shows wire colliders in front, and selects the new render mesh and cages.
5. Inspect the complete set. Save As `chair-collision-complete.blend` to a separate path.

These are alternative routes. Do not run the completion script on the already-completed file. To revert, reopen the saved input without saving changes. Script does not save or export automatically.

## What changes

Creates a new `POC_Complete_Collision_Preview` collection. Evaluates the repaired chair into a separate render mesh `SM_Chair_Demo`, retaining UVs/materials and recording provenance. Source modifiers remain live on the original hidden `SM_Chair`. Original five manual collider meshes/transforms are unchanged; their visibility is turned off to avoid duplicate contacts at export.

The 19 closed convex collision pieces cover: seat; four legs; two outer back posts; two back rails; four individual slats; four aprons under the seat; two side stretchers. Uses `UCX_SM_Chair_Demo_00` through `_18`. Some are oriented box envelopes; leg proxies use convex envelopes of several mesh height bands, with all four proxy bottoms deliberately flattened at Z=0. This replaces approximate symmetric manual leg placements with geometry-fitted asymmetric proxies. Parts remain approximations and may overlap near joints; they are intended for one rigid body, not 19 separate actors.

All collider geometry is baked in mesh coordinates with identity object transforms and shared world origin. Wireframes are viewport helpers; colliders are hidden in final renders. The collection is intended for later selective export, not Export All. The old manual UBX meshes and Boolean cutters must not be included in the Unreal asset export.

## Verified locally on Andy's actual file

Official bpy 5.1.2. Successful run and saved/reopened result: 19 convex, closed, positive-volume meshes, at most 15 vertices each; 4 foot minima exactly Z=0. Fifteen rays through the five backrest gap centres at three heights and one ray under the chair centre miss all collision pieces. These are sampled clearance checks, not exhaustive swept-volume guarantees. Render mesh retains 72,664 triangles, valid UV/material references and original bounds: height .999956965 m. Original source/manual geometry and transforms, source UVs and all packed texture pixel digests unchanged. Repeat-run guard tested. Front/rear Cycles CPU renders with temporary cyan hull-edge overlays inspected. Temporary QA cameras/lights/wire curves are not in the delivered file.

The generated `POC_collision_report.json` Text datablock records per-part counts/volume, provenance, clearance samples, support heights and limitations. To view it, select it from the Text Editor's text selector.

## Not yet verified

No Unreal import, collision cooking or Chaos simulation has run. Scale is a one-metre demo assumption, not a measured chair. Mass, friction and inertia remain unset/unverified. Flat proxy feet do not establish real physical stability. Materials still have generated texture/shading artifacts. No fracture or structural load validation is implied.

## Next checkpoint

Andy reviews the whole completed collision preview once. Adjust any obvious fit problems together. Then automate selective FBX export plus explicit textures/material mapping, verify Unreal version and import settings, and run/record the Chaos drop and tip demonstration. Collision prefix/name matching follows Epic's FBX static-mesh documentation: https://dev.epicgames.com/documentation/unreal-engine/fbx-static-mesh-pipeline-in-unreal-engine .
