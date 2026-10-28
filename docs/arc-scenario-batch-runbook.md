# Hosted ARC prompt-to-plan CLI

Prerequisite: hosted API access succeeded with gpt-oss-120b on October 18. Use the existing main branch. This is a lightweight API client and layout builder, not GPU inference on a login node; no sbatch job or Python dependency installation is needed.

The frontend room studio is the normal entry point; this CLI remains useful for explicit experiments and saved-plan replay. Hosted planning and downstream chair room assembly have user-confirmed runtime evidence. See [current status](current-status.md) and [studio guide](studio-pipeline-runbook.md).

## Explicit CLI run

```bash
cd "$HOME/emergency-training-poc"
git pull --ff-only
python3 arc/scripts/generate_scenario_batch.py
```

Paste your personal key only at the hidden terminal prompt. It is not saved. The built-in natural-language request asks for three classroom-style chair layouts, two with a clear designated aisle and one with an obstruction. The actual request goes to ARC's hosted model; no fixture is substituted when the API or validation fails.

The program prints a new output directory. If ARC_PROJECT_WORKSPACE is exported, outputs go beneath its scenario-batches folder; otherwise they go beneath arc/results/scenario-batches in the checkout. Original chair generation outputs remain untouched. Existing destination directories are rejected.

Use Open OnDemand's Files browser to find that printed folder and download it. Open preview.html from the extracted/downloaded folder in your PC browser. Keep the SVG files beside it. Alternatively view the individual room_001.svg etc. The preview shows top-down geometry: brown chairs, green designated aisle and doorway, red chairs intersecting the aisle.

Return plan.json, manifest.json and one screenshot of the preview. No credentials belong in these files. Inspect the model's assumptions and whether its plan actually matches your intended request; a structurally valid plan is not proof of semantic fidelity.

## Your own prompt and N variants

Write a UTF-8 text file, e.g. prompt.txt, containing the request. Then:

```bash
python3 arc/scripts/generate_scenario_batch.py --prompt-file prompt.txt --count 3 --seed 20261018
```

Supported scope: rectangular classroom-like room, 6-10m wide/deep, one centred positive-Y doorway, registered wooden chairs, designated central aisle, clear/obstructed conditions, 1-30 variants and 4-20 chairs per room subject to capacity checks. Unsupported desks, smoke, characters, new assets or other capabilities cause rejection when identified by the model; the interpreted plan still requires human review. Placements use constrained seeded sampling, not arbitrary LLM coordinates. An aisle overlap does not prove an exit is impassable; alternate routes may exist.

A large chair count in a small room can be infeasible. The builder rejects it instead of shrinking objects or silently reducing the count. Revise the request if that happens. Invalid JSON, unknown fields/assets, nonfinite numbers and inconsistent geometry are rejected; model output is never executed as code. API errors use the existing sanitized diagnostics. Do not retry by hand-editing generated output to bypass validation.

## Replay without a model call

```bash
python3 arc/scripts/generate_scenario_batch.py --replay-plan /actual/path/to/plan.json --seed 20261018 --output /actual/path/to/new-replay-folder
```

Replace the example paths with actual paths. Replay uses variant conditions/count from the saved plan. The same plan, seed and script revision reproduce the spatial scene JSON. A seed alone does not reproduce a fresh hosted LLM response. request.json records whether the source was live or replay; hashes cover the plan and emitted package files. The output is staged and only published after all layouts pass.

## Files and next boundary

- plan.json: actual model interpretation after validation.
- request.json: original prompt, seed, model/source metadata and response-content digest. Raw reasoning and API credentials are not retained.
- room_NNN.json: spatial draft, metre coordinates, Z-up, named rotation fields, doorway and explicit geometric check.
- preview.html / room_NNN.svg: whole-batch review.
- asset-registry.json: chair identity, assumed dimensions, generation provenance. Binary assets are excluded from the portable package; local workers validate the configured reviewed-chair binding.
- manifest.json: hashes/stage. Generation alone does not prove assembly; actual worker outputs/reports are separate evidence.

This CLI emits the plan/layout package. Implemented local Blender and Unreal consumers operate downstream through the studio or manual package route. Fresh furniture generation is a separate asset workflow; evacuation behavior is not simulated or validated by layout generation. The deterministic session engine and legacy mock authoring endpoint are separate; room plans are not automatically published training scenarios.

Validation before first live run: offline invalid-plan tests, duplicate/nonfinite JSON rejection, 540 layouts across room sizes/seeds and conditions, over-capacity rejection, deterministic replay, file digests and no-overwrite behavior. Compilation/lint pass. The user subsequently confirmed live frontend planning and room assembly. Retain the actual plan/request/worker records for each new run rather than inferring semantic compliance from that earlier success.
