# Furniture variants and the optional manual handoff

The default is now **Asset library -> Describe it. Build it.** Follow the
[automation guide](asset-automation-runbook.md) for description-generated references,
frontend Slurm jobs and automatic retrieval/preparation. This guide preserves the
optional existing-PNG/request/result ZIP route for setup, comparison and recovery.

A family can have many designs: dining/folding/armchair, two-seat/three-seat/sectional.
Many instances of one design should reuse one asset. The reviewed chair remains
the only room/Chaos binding; a new variant is not automatically room-compatible.
[Current status](current-status.md).

## Local setup and manual request

Update from `main` using the [workspace guide](arc-workspace-runbook.md). Preserve
private configuration and saved files. Open the one-port app at 127.0.0.1:8772.

1. Open **Asset library -> New variant** for the manual image form.
2. Enter family, design name/description, target width/depth/height and seed.
3. Supply a whole single-object reference PNG. The prepared charcoal couch reference
   is an image, not generated geometry. PNG bounds are 64-4096 pixels per side, under 8 MB.
4. Save the request and download its ARC request ZIP. This local save submits no GPU job.

Hunyuan is image-conditioned. In this route, description is metadata; it does not
add text conditioning to the model. In the automatic route, description drives
actual SDXL reference generation first. The older couch target is 1.8 x .85 x .85 m,
seed 42; keep or explicitly change it.

## Upload and submit manually

Use your authenticated ARC shell/Files interface and VPN as needed. Upload the
request ZIP intact. In the ARC checkout:

```bash
cd "$HOME/emergency-training-poc"
git status --short --branch
git fetch origin
git switch main
git pull --ff-only
bash arc/scripts/submit_hunyuan_variant.sh "$HOME/asset-request-ACTUAL_SHORT_ID.zip"
```

Use the actual downloaded filename. Preserve changed tracked files and ignored
`arc/.env`; stop if updating fails instead of discarding work. The script uses the
configured account/partition/QoS and existing verified shape/paint runtimes. It does
not require the hosted planner API key or a runtime rebuild.

Record the actual `Submitted batch job NNNNNNN` ID, then inspect:

```bash
squeue -j JOB_ID
sacct -j JOB_ID -X --format=JobID,State,ExitCode,Elapsed
tail -n 30 arc/results/hunyuan-variant-JOB_ID.out
tail -n 80 arc/results/hunyuan-variant-JOB_ID.err
```

Replace `JOB_ID`. The successful log prints the exact reusable `result.zip` path
under `$ARC_PROJECT_WORKSPACE/hunyuan21/variants/FULL_ASSET_ID/`. Download that ZIP,
not the runtime or model cache. Review/sanitize logs before sharing.

This manual route does not populate the frontend automation scheduler tracker.
It reuses a completed exact-variant result; file locking prevents simultaneous
generation of the same variant. The automatic dispatch journal/reconnect behavior
is a separate lane. Never create another job simply because a network reply was lost.

## Import and prepare

1. Select the saved design and import its actual `result.zip`.
2. Inspect the returned GLB; reference imagery is not result geometry.
3. Run the design card's Blender preparation action using configured local Blender.
4. Download `furniture-unreal.blend`, `unreal-package.zip`, preview and report.
5. Inspect the whole result, then follow the automation guide's Unreal import steps.

The current preparation action uses real scoped Blender MCP: preserved source,
conservative cleanup, uniform height matching, floor/center pivot, CPU convex
decomposition and checked export. It reports actual dimensions and flags mismatches;
it does not stretch width/depth or reconstruct arbitrary missing/fused parts.
Earlier saved `furniture-review.blend` files remain historical staging outputs.

The generic Unreal importer still needs its first live engine/cooking check. A
successful prepared package is a review candidate, not physical certification or
an automatically registered room asset.

## Identity and storage

Variant identity binds family/name/description, target dimensions, reference bytes,
seed/settings and pinned source/model revisions. Exact matches reuse one design;
this is not semantic similarity. Upstream paint defaults do not imply bitwise
regeneration. Result import checks request/reference/stage identities, revisions,
hashes and bounded embedded resources, then retains the source and notices.

App data lives under ignored `logs/studio/asset-library/` with SQLite records.
Scenario Trash does not delete reusable designs. No credentials belong in request
or result ZIPs. Before mixed rooms, extend planner IDs/footprints, registry reuse
and Blender/Unreal bindings together. Never fulfill a couch request with a chair.
