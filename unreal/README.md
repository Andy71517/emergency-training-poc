# Future Unreal Client

Unreal is a future presentation and input client. It is not the source of truth.

Later, Unreal may render scenario state and send trainee actions back to the backend. The backend still owns ordering, state changes, validation results, and logs.

The first Unreal slice should be a text-only debug display. It should render the backend-owned phase, validation status, warnings/errors, and environment object rows from `contract/debug-display-state.schema.json`.

This repo does not include an Unreal project, scene, gameplay logic, networking topology, projection mapping, sensing integration, or 3D content. `EmergencyTrainingClient/` is only a reserved location.

The thin client contract lives here:

- [contract/client-contract.md](contract/client-contract.md)
- [contract/client-state-machine.md](contract/client-state-machine.md)
- [contract/state-display-contract.md](contract/state-display-contract.md)
- [contract/debug-display-state.schema.json](contract/debug-display-state.schema.json)
- [contract/examples/](contract/examples/)

Keep scenario authority, validation, logging, and review generation in the backend.
