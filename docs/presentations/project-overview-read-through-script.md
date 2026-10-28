# FIELDWORK practice script

Updated October 28, 2026; follows the eight-slide deck.

## 1. FIELDWORK

The goal is to describe an environment and get editable assets and a scene we can
review in Blender and Unreal. The longer-term destination is adaptive emergency
training. Today I can show concrete parts of that path and the checks still ahead.

## 2. Foundation

The backend still owns accepted state, validation and evidence. Two small toy
scenarios let me replay actions and explain findings. That remains useful as the
visual tools grow; a generated room alone does not define a training scenario.

## 3. Room studio

The studio calls ARC's hosted planner and builds seeded room layouts. The working
room lane reuses a reviewed generated wooden chair. Blender room assembly and the
Unreal maps and Chaos batches have been confirmed in actual use.

## 4. Asset workflow

The new asset lane starts with a description. It generates a reference internally,
runs Hunyuan shape and paint on ARC, retrieves the result and uses Blender MCP for
conservative cleanup, collision proxies and export. It saves an editable Blender
file and an Unreal import package. The source and provenance remain available.

## 5. Evidence

The accepted chair has nineteen collision pieces. The new generic preparation was
run with real Blender, MCP and CoACD on a synthetic fixture and produced twenty-eight
closed pieces. That validates machinery; it does not mean the couch was generated.
The implementation also passed the backend/ARC tests and frontend/CI checks.

## 6. Next acceptance

The first live automated couch needs the one-time SSH setup and ARC source update.
Then I need to inspect the actual model, check the generic package in Unreal and
verify a real recording. Mixed-furniture room planning and bindings come together next.

## 7. Boundaries

This is still local and single-user. Automatic cleanup cannot reconstruct arbitrary
missing parts. Engine movement and collision proxies do not establish calibrated
physical accuracy, clinical validity or training effectiveness.

## 8. Review

I would like feedback on whether the whole-result review makes the evidence clear,
and which room and furniture combination would be most useful for the next proof.
