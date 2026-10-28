# Local logs and saved workspace

| Location | Contents |
| --- | --- |
| `sessions/` | Ordered JSONL actions, findings and snapshots for replay/review |
| `physics/` | Browser primitive proof authorizations/observations |
| `studio/` | SQLite jobs/assets, plans/packages, Blender outputs, engine commands/results and recordings |
| `studio/asset-library/` | Variant requests, references, imported models, preparation runs and reports |

These files are ignored by Git. Back up important evidence before removing local
data. Session state is in memory while session JSONL persists; studio jobs/assets
persist across backend restarts.

Batch Delete moves a record to recoverable Trash. It does not free disk space,
delete reusable assets or remove maps from an external Unreal project. There is
no permanent-delete control in the app. Do not delete worker data during active jobs.

Use synthetic identifiers and non-sensitive prompts; never put credentials, patient,
trainee or real operational data in logs or support screenshots. Read native worker
logs locally and sanitize before sharing. [Data handling](../docs/security/logging-and-data-handling.md),
[history](../docs/batch-history-and-assets.md), [current status](../docs/current-status.md).
