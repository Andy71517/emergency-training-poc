# Future Unreal Client

Unreal is a future presentation and input client. It is not the source of truth.

Later, Unreal may render scenario state and send trainee actions back to the backend. The backend still owns ordering, state changes, validation results, and logs.

The first Unreal slice should be a text-only debug display. It should render the backend-owned phase, validation status, warnings/errors, and environment object rows from `contract/debug-display-state.schema.json`.

This repo does not include an Unreal project, scene, gameplay logic, networking topology, projection mapping, sensing integration, or 3D content. `EmergencyTrainingClient/` is only a reserved location.

`EmergencyTrainingClient/` now includes a tiny starter scaffold for that future debug display:

- local sample display-state JSON
- a panel-field config
- beginner notes for the first Unreal implementation pass

It is still not a full Unreal project.

The next Unreal step is sample JSON first:

- create a blank Blueprint project
- read one checked-in display-state JSON file
- show a text-only debug panel
- keep all scenario authority in the backend

See [EmergencyTrainingClient/Docs/read-sample-json-debug-panel.md](EmergencyTrainingClient/Docs/read-sample-json-debug-panel.md).

The thin client contract lives here:

- [contract/client-contract.md](contract/client-contract.md)
- [contract/client-state-machine.md](contract/client-state-machine.md)
- [contract/state-display-contract.md](contract/state-display-contract.md)
- [contract/debug-display-state.schema.json](contract/debug-display-state.schema.json)
- [contract/examples/](contract/examples/)

Keep scenario authority, validation, logging, and review generation in the backend.
