# Session display scaffold

This folder preserves the early text/JSON display starter. It is not a complete
Unreal project and is not the user's external chair/room demo project. Current
editor scripts and bridge are documented in [unreal/README.md](../README.md).

The scaffold contains panel fields, clean/warning/hallway JSON samples, generated
sample text and beginner display notes. Refresh the sample text from the repo root:

```powershell
python scripts/write_unreal_debug_text.py
```

Use [debug-display-starter](Docs/debug-display-starter.md) and
[sample JSON guide](Docs/read-sample-json-debug-panel.md) only when working on this
session-client experiment. A full trainee WebSocket client is still unimplemented;
the local editor job bridge is a different protocol.

The backend owns scenario state, validation and review. The scaffold does not
certify physics, scoring or emergency guidance. [Current status](../../docs/current-status.md).
