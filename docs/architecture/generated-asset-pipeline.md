# Future Generated-Asset Pipeline

**Status:** documentation only. No assets are generated now.

A later experiment might use Hunyuan 3D or similar tools to create candidate meshes. Those files should be treated as drafts until they pass review.

The first future POC object should be a simple wooden chair. A chair is realistic for the kinds of rooms this simulator cares about, and it gives future physics tests something useful to collide with, move, tip, or block.

The scenario also tracks a simple entry door. The door's open/closed state can affect the deterministic backend flow now, while lock state, type, hinge, collision, mass, and force direction details stay as future-facing metadata.

For physics later, mass is not enough by itself. Gravity needs a real physics body, collision shape, scene transform, material/friction settings, and an engine that updates the object over time. The current repo only records preview metadata.

A future asset flow should include:

- generation
- metadata capture
- format checks
- human safety and content review
- optimization
- provenance and licensing review
- explicit promotion into a reviewed folder

A generated file is not approved just because it exists. Scenario correctness should never depend on visual details from generated assets.
