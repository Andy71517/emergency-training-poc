# Prompt-to-scene batch: scoped implementation plan

## Current evidence

The chair geometry and PBR texture jobs ran on ARC. Blender cleanup, export and collision preparation ran in Blender 5.1.2. Unreal 5.8 imports/materials/simple collision and gravity/contact/settling have user runtime evidence. The direct component repair `unreal/scripts/repair_chair_presentation_v3.py` resolved the inverted presentation. Andy confirmed the tilted chair falls, rocks and settles upright. Returned video is 11.5145 seconds, 2416x1440, approximately 59.94fps. Sampled frames show raised starting positions, drop and resting chairs with a stationary reference. This is a visual demonstration, not calibrated physics.

Existing authoring service is explicitly a local mock: `backend/app/authoring/service.py` and its README. Existing pipeline Pydantic records cover provenance/review/publication, but are not executors. `schemas/pipeline/published_scenario_package.schema.json` does not specify room geometry or object transforms. Existing scenario YAML describes deterministic training state, not a spatial scene.

## Chosen route

Use the ARC hosted chat-completions service for bounded scenario authoring, without a new self-hosted LLM environment. Official endpoint: https://llm-api.arc.vt.edu/api/v1/chat/completions. Documented model example: gpt-oss-120b; actual user access is still to be checked. Personal key stays in Andy's runtime, never in Git/chat/job logs. Do not send keys to the assistant. The first prepared command is the small stdlib access checker, not a model build or generation job.

Source: https://docs.arc.vt.edu/ai/011_llm_api_arc_vt_edu.html (reviewed October 18, 2026).

## Concrete changes for the scene batch

1. Add a versioned spatial scene specification alongside the existing contracts: metres, Z-up, named rotation axes, room extents, a doorway interval, a permitted asset inventory, per-instance transforms and fixed test conditions. Separate authoring proposals from approved spatial packages. Do not replace the deterministic backend state machine.
2. Add a bounded ARC prompt adapter: short JSON plan, allowed asset IDs, strict parsing, dimension/count limits, unsupported-feature errors and recorded original request/model/response digest. No model-generated code is executed. Network/model errors must not silently substitute a fixture. Separate saved-response replay from fresh LLM calls: a random seed does not make hosted model output reproducible.
3. Expand the validated plan deterministically into three layout variants using saved seeds. First scope: a classroom-like room, a fixed doorway, chair instances and a defined aisle/corridor region. Check room containment, pairwise footprint conflicts and specified corridor overlap. Label that result as a geometric corridor check; it is not navigation, accessibility or evacuation validation. Include a clear case and an intentionally obstructed case. Requests for unsupported desks/smoke/agents must be rejected or explicitly revised, not silently represented as chairs.
4. Register the reviewed chair and its actual dimensions/provenance/content hashes. Reuse prepared geometry/maps/collisions. No new Hunyuan job is required for these three variants. Fresh-asset generation is a subsequent extension of the registry resolver, not implemented by this batch.
5. Write portable JSON, layout previews and stage records on ARC. A replay command rebuilds from the saved validated plan and seeds without another LLM request. A count argument supports bounded N; demonstrate three first.
6. Blender 5.1.2 assembler reads the exact package, builds dimensioned walls with a real doorway gap and instances the reviewed chair. Produces a separate reviewed scene/export and fails on missing/changed inputs. Entire layout inspection once. Room geometry is procedural from ARC-produced instructions; it is not a monolithic Hunyuan room mesh.
7. Unreal 5.8 assembler consumes the same approved specification and prepared assets. Converts metres to centimetres once, checks the conversion/axes/door opening, constructs separate levels, and uses explicit component transforms plus readback checks learned from the chair repair. Static room/collision and selected movable chair props. No occupant agent, smoke solver, calibrated physics or backend integration is claimed.
8. Run meaningful validation on invalid LLM outputs, geometry/layout constraints, deterministic replay and path/hash handling; use Blender runtime for assembly/export checks. Unreal execution remains user-run integration testing. Retain intermediate artifacts for stage-only retries.

## Completion criteria

One natural-language request really reaches ARC's hosted model; its saved and validated interpretation produces three reproducible spatial variants; Blender and Unreal load those same transforms without manual furniture placement; user reviews complete scenes and captures one room-level demonstration. API authentication, prompt generation, Blender scene assembly and Unreal assembly are separate progress checkpoints. Do not call the end-to-end batch complete at the access-check stage.

## First user action

Open https://llm.arc.vt.edu. User profile > Settings > Account > API keys. Create or reuse a personal key; keep it private. From the current ARC checkout after pulling the Unreal branch, run `python3 arc/scripts/check_scenario_planner_access.py` and paste the key only into its hidden terminal prompt. Share only the resulting non-secret status lines. No sbatch command is needed for this tiny API check. Successful authentication does not yet verify JSON planning behavior.
