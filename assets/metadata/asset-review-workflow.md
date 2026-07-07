# Asset review workflow

**Status:** planning workflow only. No generated or reviewed assets exist yet.

This workflow explains how a future generated asset should move through the repo.

The main rule:

> Nothing generated goes straight into Unreal.

## Folder flow

Use this path later:

```text
generated candidate
  -> assets/generated/
  -> Blender/manual review
  -> metadata decision
  -> assets/reviewed/ only if approved
  -> future Unreal import only after review
```

## Step 1: create or collect a candidate

A candidate might come from:

- Hunyuan 3D or a similar model
- a manually made Blender object
- a licensed asset source
- a placeholder object made for testing

Put unreviewed candidate files in:

```text
assets/generated/
```

Do not commit large generated files unless the project is intentionally testing the asset pipeline.

## Step 2: record source metadata

Before review, create or update a metadata file.

Use:

```text
assets/metadata/asset-review-template.md
```

Record:

- asset name
- source or generation tool
- prompt/source reference
- date
- license/provenance notes
- intended use
- reviewer
- review status

## Step 3: inspect in Blender

Open the asset in Blender and use:

```text
assets/metadata/blender-review-checklist.md
```

Check:

- scale
- orientation
- origin/pivot
- floor contact
- mesh quality
- materials
- obvious generated weirdness
- collision-readiness
- Unreal import readiness

## Step 4: decide status

Use one of these:

- `candidate`
- `needs_changes`
- `reviewed_visual_only`
- `reviewed_collision_candidate`
- `rejected`

If the asset is only visual, say that clearly.

If it might be useful for collision later, still say physics has not been validated.

## Step 5: promote only after review

Only move an asset to:

```text
assets/reviewed/
```

after source/provenance, Blender, and human review are complete.

Reviewed does not mean medically accurate, operationally accurate, physically accurate, or training-approved.

It only means the asset passed this repo's POC asset-quality gate.

## Step 6: future Unreal import

Unreal import comes after review.

The first Unreal import should still be boring:

- one object
- one blank scene
- no gameplay
- no physics claims
- backend still owns scenario state

## What this workflow avoids

This avoids:

- random generated files in the repo
- assets with unclear origin
- broken meshes entering Unreal
- visual details being mistaken for scenario truth
- fake realism
- accidental overclaiming

