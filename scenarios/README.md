# Scenarios

Scenario YAML files define the toy worlds used by the POC.

Each scenario should be small and readable. It should include the starting state, allowed actions, transition rules, validation hints, end conditions, and the expected happy path.

The current smoke-room scenario includes a wooden chair, an entry door, and a smoke/visibility cue as environment state. The chair can block the entry path until `move_obstacle` clears it. The door starts closed and blocks entry until `open_door` opens it. The smoke/visibility cue starts unchecked until `check_visibility` records that the cue was noticed.

For now, these are deterministic software cues only. Door lock state, door type, hinge side, swing direction, collision shape, mass, force directions, smoke behavior, and visibility behavior are metadata.

These scenarios are software fixtures, not medical guidance, clinical validation, firefighter/EMT protocol, or certification material.

Keep them versioned, reviewable, deterministic, and free of hidden executable logic.
