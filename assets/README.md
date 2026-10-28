# Assets and review

The project has a real generated/reviewed wooden-chair baseline and a reusable
chair/couch variant library. Source-controlled folders here hold review guidance;
the large binary assets are not bundled in Git.

- Current app library: ignored `logs/studio/asset-library/` plus SQLite records.
- ARC weights/generated outputs: configured project storage.
- Accepted chair Blender file: private `CHAIR_BLEND` path on the workstation.
- [generated/](generated/README.md): optional local staging, unreviewed by default.
- [reviewed/](reviewed/README.md): optional explicitly promoted local assets.
- [metadata/](metadata/README.md): provenance/review guidance and toy object notes.

Use [description-based automation](../docs/asset-automation-runbook.md) or the
[manual reference route](../docs/furniture-variants-runbook.md). The existing room
demo uses the reviewed wooden chair. New variants need actual review and coordinated
room bindings; library presence or successful Blender preparation does not approve them.

[Current evidence](../docs/current-status.md),
[review workflow](metadata/asset-review-workflow.md),
[Blender checklist](metadata/blender-review-checklist.md).
