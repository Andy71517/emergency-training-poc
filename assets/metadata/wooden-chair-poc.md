# Wooden Chair POC Object

**Status:** future asset candidate only. No mesh exists yet.

Use a simple wooden chair as the first environmental-object model when the asset pipeline is tested.

Why this object:

- A chair is common in rooms, stations, training spaces, and public buildings.
- It is easier to justify in emergency-response scenarios than an abstract test object.
- It can later support basic physics checks: collision, tipping, blocking movement, mass assumptions, and object placement.
- It is simple enough to review without turning the POC into an asset-production project.

Do not generate, import, or approve a chair asset yet. This note only records the preferred first candidate.

## Physics preview modes

The local demo can show the chair in two static preview modes:

- `physics_enabled: false`: the chair is visual/context metadata only.
- `physics_enabled: true`: the chair is marked as a future physics candidate for later collision, tipping, blocked movement, mass, and placement checks.

Neither mode runs a physics engine. No mesh, collision shape, Unreal import, or generated asset exists yet.
