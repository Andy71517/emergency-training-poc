# Generation pipeline records

Versioned provenance/review/publication records:

- `arc_generation_job.schema.json`: generation lifecycle and reproducibility record.
- `asset_artifact_manifest.schema.json`: candidate provenance and file inventory.
- `blender_asset_review.schema.json`: refinement/review outcome.
- `published_scenario_package.schema.json`: instructor-approved publication record.

These schemas are records, not executors. The implemented studio/asset services
and ARC/MCP workers have their own bounded request/package contracts. Do not assume
these generic records are the exact live HTTP or scene-layout payloads.

The legacy authoring module still uses fixture drafts; real hosted room planning
is a separate service. Publication of a validated training scenario and mixed-asset
runtime integration remain open work. [Schema map](../README.md),
[current status](../../docs/current-status.md).
