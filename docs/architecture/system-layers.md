# System layers

[Current status](../current-status.md) records which layers have live evidence.

| Layer | Current responsibility |
| --- | --- |
| React studio | Prompts, previews, jobs/assets/history, review/downloads and fixed worker controls |
| FastAPI API | Validated HTTP/WebSocket boundaries; no browser authority over state or shell commands |
| Studio service | SQLite jobs/assets, hosted model planning, seeded scene packages, reuse, Trash, worker evidence and recordings |
| ARC transport/generation | Backend-owned SSH RPC; persistent dispatch journal; Slurm SDXL/Hunyuan job; bounded result retrieval |
| Blender MCP/local workers | Fixed asset inspection/preparation tools and room assembly; copied source, convex decomposition, exports and reports |
| Unreal editor bridge | Local command-file polling; map assembly, Chaos observations and recording work in the user's external project |
| Session engine | In-memory ordered actions, deterministic YAML transitions and explicit toy-rule validation |
| Logging/review | JSONL sessions/physics, SQLite studio state, replay and human-readable evidence |
| Legacy authoring | Separate in-memory fixture suggestions, edits and revision-specific approval |

The studio persists under ignored `logs/studio/`; sessions remain in memory while
their JSONL records are saved. The two persistence models are intentional and
should not be described as a database-free application.

Model plans are data, not code. The backend owns accepted plans, action ordering,
state, validation and review. Engines report physical observations; people review
generated assets and training meaning. The editor bridge is separate from the
future trainee WebSocket client.

CS Launch hosting, multi-site networking, sensing, projection and real-time AI
adaptation remain future work. Current asset/room worker details are in the
[asset runbook](../asset-automation-runbook.md) and [studio guide](../studio-pipeline-runbook.md).
