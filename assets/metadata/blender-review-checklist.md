# Manual Blender review checklist

**Status:** future asset review checklist. No assets are reviewed yet.

Generated assets should not go straight into Unreal.

Open them in Blender first and check the basics.

This checklist is for asset quality control only. It does not prove real physics, medical realism, operational safety, or training correctness.

## Review status labels

Use these labels in asset metadata:

| Status | Meaning |
| --- | --- |
| `candidate` | Generated or sourced, but not reviewed yet. |
| `needs_changes` | Opened in Blender and found problems. |
| `reviewed_visual_only` | Good enough for visual/context use only. |
| `reviewed_collision_candidate` | Clean enough to test simple collision later. |
| `rejected` | Should not be used. |

No asset should be treated as approved just because it exists in `assets/generated/`.

## Minimum Blender workflow

1. Open the candidate file in Blender.
2. Save a screenshot for review notes if useful.
3. Check scale, orientation, origin, and floor contact.
4. Inspect mesh quality.
5. Inspect materials.
6. Decide whether the asset is visual-only, collision-candidate, needs changes, or rejected.
7. Record the decision in an asset metadata file.
8. Only promote the file to `assets/reviewed/` after explicit approval.

## Required checks

### Identity and source

- Asset name is clear.
- Source tool or source site is recorded.
- Prompt or source reference is recorded if generated.
- Creation date is recorded.
- Reviewer name/date are recorded.
- License or usage notes are recorded.
- File format is recorded.
- The asset has not been promoted without review.

### Scale, orientation, and placement

- Scale looks believable for the scenario.
- Units are understood.
- Object faces the expected direction.
- Object origin/pivot is in a useful place.
- Object sits correctly on the floor or expected surface.
- Door/chair pivots make sense if the object might move later.

### Mesh quality

- Geometry is not broken, inside-out, or wildly messy.
- There are no obvious floating fragments.
- There are no huge hidden meshes far from the object.
- Polygon count is reasonable for a POC scene.
- Normals look correct enough for a preview.
- The mesh can be selected and moved cleanly as one object or a clear object group.

### Materials and appearance

- Materials are simple and not misleading.
- Textures are not obviously corrupted.
- Colors/materials match the intended object well enough for a POC.
- No text, logos, personal data, or weird generated markings are present unless intentionally approved.

### Unreal-readiness

- Object name is clear and stable.
- Export format is recorded.
- Expected Unreal import scale is recorded.
- Expected Unreal folder/location is recorded.
- Any known import warnings are recorded.

## Physics-readiness checks

- Simple collision shape can be made later.
- Mass estimate is written down as an assumption.
- Object dimensions are recorded or estimated.
- Door/chair/obstacle pivots make sense for future motion.
- Collision needs are described in plain language.
- The object is not assumed to be physically correct just because it looks okay.
- Nothing implies real physics has already been validated.

## Reject or pause if

- The source or license is unclear.
- The object is wildly wrong for the scenario.
- The mesh is broken beyond quick cleanup.
- The file is too heavy for a POC test.
- The object includes inappropriate, copyrighted, personal, or confusing visual details.
- The asset would make the demo look more authoritative than it really is.

## Approval language

Use careful wording:

Good:

> This asset is reviewed for visual POC use.

Also good:

> This asset is a future collision candidate, but physics has not been validated.

Avoid:

> This asset is realistic and ready for training.

Passing this checklist only means the asset is clean enough for the next POC step.
