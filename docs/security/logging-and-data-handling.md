# Logging and data handling

| Location | Data |
| --- | --- |
| `logs/sessions/` | JSONL messages, attempted actions, findings, ordered state snapshots and IDs |
| `logs/physics/` | Browser proof configuration, authorization and reported observations |
| `logs/studio/` | SQLite job/asset records, prompts/plans, files, previews, native reports/logs, engine command/results and recordings |
| ARC project storage | Model cache, generated references/models, dispatch journal, stage manifests and scheduler logs |
| External Unreal project | Maps/assets, saved engine reports and generated content |

Use synthetic identifiers and non-sensitive briefs. Do not use real trainee,
patient, medical, emergency or private operational data in this POC. A spatial
generation prompt is sent to the configured provider; it is not purely local.

Keep private `.env` files, API keys, SSH private keys, passphrases and Duo codes out
of Git, prompts, browser storage, request ZIPs and screenshots. Credential filtering
reduces accidental leakage; it is not a comprehensive secret-discovery service.
Inspect native logs locally and sanitize paths, identifiers and content before sharing.

These local data folders and raw ARC results are ignored by Git. Commit sanitized
contracts/fixtures and review guidance, not generated models/weights or private data.
Back up important evidence before manual cleanup. Retention is manual; there is no
automatic archival/production deletion policy.

Batch Trash is recoverable and retains files. It does not erase asset-library data,
ARC outputs or external Unreal maps. Do not remove active worker folders. Future
multi-user deployment needs access controls, consent, retention/deletion, quotas,
audit and provider data-handling decisions before real data is introduced.

[Storage guide](../../logs/README.md), [history](../batch-history-and-assets.md),
[security overview](README.md).
