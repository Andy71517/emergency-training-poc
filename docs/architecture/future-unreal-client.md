# Future Unreal Client

**Status:** future presentation client. The current repo only defines the contract.

Unreal may eventually render scenario state, collect trainee interactions, and show feedback. For now, it should be treated as a future client, not the brain of the system.

The contract lives in `unreal/contract/`. You can exercise it with `scripts/run_unreal_contract_harness.py`.

That harness behaves like a future thin Unreal shell:

1. Open the WebSocket.
2. Send `start_session`.
3. Send one ordered action at a time.
4. Receive state updates from the backend.
5. Stop when `scenario_ended` arrives.

No full Unreal scene, rendering layer, gameplay framework, networking topology, projection mapping, sensing integration, or generated content is required now.

The next Unreal step is a text-only debug display. It should show backend state such as phase, validation status, chair moved/not moved, door open/closed, smoke/visibility cue checked/unchecked, and path blocked/not blocked. Use `scripts/preview_unreal_display.py` to preview that display from a JSONL log before Unreal exists.

## Boundary rule

Unreal may cache and display backend state. It must not invent or change scenario progress locally.

The backend owns:

- scenario transitions
- validation results
- end conditions
- session logs
- post-scenario review inputs
