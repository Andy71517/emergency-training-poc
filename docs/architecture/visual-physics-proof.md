# Visual Physics Proof

## Status

Approved direction for the next visual-development phase.

The project will use a hybrid path:

1. Build a lightweight browser-based 3D physics preview for development and presentations.
2. Reproduce the bounded proof in Unreal Engine 5.8 using Chaos Physics.
3. Replace primitive geometry with a reviewed generated asset only after the interaction works.

The web preview is useful evidence and a long-term developer tool. Unreal remains the intended immersive runtime.

## What physics means in this proof

Physics means that a configured object responds to movement, gravity, mass, and physical contact inside a real-time physics engine.

This first proof does not attempt to validate an exact real-world chair model. It verifies that the integration can:

- create a rigid body with a fixed mass
- apply a backend-authorized movement interaction
- simulate gravity
- detect contact with the floor or another configured collider
- let the object move, rotate, tip, and settle
- report observable results to the backend for logging and review

Gravity and mass are constants for one test run. The interaction and resulting movement/contact evidence are the variables being observed.

## First acceptance test

The first test object is a chair represented by primitive geometry. It begins upright on a floor and faces a short, clearly visible contact barrier.

When the backend authorizes the test, the physics client applies one fixed impulse toward the barrier at an elevated point on the chair. This should produce visible translation and some rotation before the chair contacts the barrier or tips into the floor.

The browser presents this as one short sequence:

```text
ready
  -> backend authorizes interaction
  -> fixed impulse is applied
  -> movement threshold is reached
  -> contact is detected
  -> chair settles or the observation window ends
  -> evidence is sent to the backend
```

### Fixed configuration

- coordinate units: meters, kilograms, and seconds
- gravity: `[0, -9.81, 0]` meters per second squared
- chair mass: `12` kilograms
- chair rigid-body type: dynamic
- initial chair position: versioned scene value, upright and resting on the floor
- initial chair rotation: `[0, 0, 0]`
- collider: versioned compound primitive collider matching the visible primitive chair
- chair friction: `0.65`
- floor friction: `0.75`
- restitution: `0.05`
- linear damping: `0.35`
- angular damping: `0.50`
- fixed simulation time step: `1/60` second
- interaction: one `14` newton-second horizontal impulse
- impulse point: approximately `0.70` meters above the chair's floor contact
- contact barrier: static, named `contact_barrier`, positioned in the impulse direction
- maximum observation window: `10` seconds

These are POC configuration values chosen to make the interaction visible and repeatable. They are not validated measurements of a particular real chair.

### Required observations

- backend authorization ID and interaction ID
- whether the chair's center moved at least `0.35` meters from its initial position
- maximum horizontal displacement
- maximum angular displacement
- whether the chair contacted `contact_barrier` after the impulse
- whether the chair made a new post-interaction contact with the floor
- first-contact time and contacted object ID
- the chair's final position and rotation
- whether the chair reached a settled state
- elapsed simulation time
- physics client and engine identifier
- configuration version used for the run

The chair counts as settled when both conditions remain true for at least `0.75` seconds:

- linear speed is below `0.08` meters per second
- angular speed is below `0.12` radians per second

### Initial pass rule

The proof passes when:

1. the backend accepts and authorizes the configured interaction;
2. the chair moves at least `0.35` meters from its starting position;
3. the physics engine reports a post-interaction contact with `contact_barrier`;
4. the chair never passes through or falls below the floor collider;
5. the client reports the movement, contact, final transform, and timing evidence for backend logging; and
6. the same versioned configuration passes three consecutive automated development runs.

Settling is reported but does not block the first movement/contact milestone. A later physics-quality milestone can require settling within the ten-second observation window.

One live presentation run is enough for the audience-facing demonstration. The three-run requirement belongs to automated or developer verification.

## Web-demo presentation requirements

The browser view should make the proof understandable without exposing raw field names:

- keep the whole room, chair, floor, and contact barrier visible at 100% browser zoom
- show a short plain-language status: `Ready`, `Movement detected`, `Contact detected`, and `Evidence saved`
- display gravity and mass as fixed test constants
- use one clear **Run physics proof** button and one **Reset** button
- complete the visible interaction in roughly ten seconds or less
- provide a collider-debug toggle for developers, hidden by default during presentations
- show a final evidence card with movement distance, contact target, elapsed time, and settled/not-settled status
- clearly label the view as a POC physics simulation

The frontend should not present this as a score or real-world procedure check.

## Authority boundary

The backend owns:

- whether a trainee or developer interaction is accepted
- scenario state and semantic outcomes
- the versioned physics-test configuration
- logging and instructor review

The physics client owns:

- continuous rigid-body motion
- gravity integration
- collision detection and response
- contact events
- measured transforms and velocities

The client reports observations. The backend records those observations and decides what they mean for the scenario.

The browser and Unreal do not independently decide training validity, protocol correctness, or trainee scores.

## Shared client contract needed

Before the visual implementation, add versioned structures for:

- object and asset identity
- dimensions, scale, initial position, and initial rotation
- rigid-body type and collider definition
- mass, friction, restitution, and damping
- gravity and simulation-step configuration
- authorized force or impulse command
- movement, rotation, contact, and settled observations
- final transform and engine metadata

The browser and Unreal may produce slightly different continuous results. They should use the same semantic contract and acceptance evidence, not claim frame-for-frame equivalence.

## First implementation stack

The browser preview should use:

- React
- React Three Fiber
- Three.js
- `@react-three/rapier`

The Unreal proof should use:

- Unreal Engine 5.8
- Chaos rigid-body simulation
- simple collision
- a physical material
- a constrained door only after the chair proof works

Generated assets and ARC model jobs are not prerequisites for the primitive chair test.
