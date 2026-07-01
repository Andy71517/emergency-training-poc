# Manual Blender Review Checklist

**Status:** future asset review checklist. No assets are reviewed yet.

Generated assets should not go straight into Unreal. Open them in Blender first and check the basics.

## Required checks

- Scale looks believable for the scenario.
- Object origin/pivot is in a useful place.
- Mesh sits correctly on the floor or expected surface.
- Geometry is not broken, inside-out, or wildly messy.
- Polygon count is reasonable for a POC scene.
- Materials are simple and not misleading.
- Object name is clear.
- Export format is recorded.
- Source/provenance notes are recorded.
- License or usage notes are recorded.
- Reviewer name/date are recorded.

## Physics-readiness checks

- Simple collision shape can be made later.
- Mass estimate is written down as an assumption.
- Door/chair pivots make sense for future motion.
- Nothing implies real physics has already been validated.

Passing this checklist does not make an asset medically, operationally, or physically accurate. It only means the asset is clean enough for the next POC step.
