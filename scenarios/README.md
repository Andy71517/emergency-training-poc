# Scenarios

Scenario YAML files define the toy worlds used by the POC.

Each scenario should be small and readable. It should include the starting state, allowed actions, transition rules, validation hints, end conditions, and the expected happy path.

The current smoke-room scenario includes a wooden chair and an entry door as environment state. The chair can block the entry path until `move_obstacle` clears it. The door starts closed and blocks entry until `open_door` opens it.

For now, only open/closed door state changes the scenario. Lock state, door type, hinge side, swing direction, collision shape, mass, and force directions are metadata.

These scenarios are software fixtures, not medical guidance, clinical validation, firefighter/EMT protocol, or certification material.

Keep them versioned, reviewable, deterministic, and free of hidden executable logic.
