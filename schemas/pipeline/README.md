# Generation Pipeline Schemas

These schemas and examples describe the approval-gated records that connect a
future ARC generation job, Blender asset review, and Unreal physics test.

They are contracts for fixtures and future adapters. They do not submit a job,
invoke a model, process a mesh, or run Unreal.

- `arc_generation_job.schema.json`: lifecycle and reproducibility record for a future ARC job.
- `asset_artifact_manifest.schema.json`: provenance and file inventory for a generated asset candidate.
- `blender_asset_review.schema.json`: manual refinement/review outcome.
- `published_scenario_package.schema.json`: instructor-approved scenario publication record.
