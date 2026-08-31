# ARC to Blender to Unreal Pipeline Plan

## Status

**Draft for approval.** This plan describes the first real generation and simulation pipeline. It does not claim that ARC generation, Blender refinement, or Unreal physics are implemented in this repository today.

## Goal

Prove one small, reviewable path from an instructor request to an approved scenario and an approved generated object, then test that object in Unreal physics and preserve the evidence.

The first target is deliberately narrow:

- one smoke-room scenario draft;
- one requested chair asset;
- one reviewed chair exported from Blender;
- one Unreal scene with a floor and contact barrier; and
- one repeatable movement and contact test.

The purpose is feasibility evidence for the future simulator, not clinical validation, responder assessment, or a real-time generation claim.

## Architecture Principle

MCP is the controlled operator interface. It is not the source of truth or the pipeline runtime.

```text
MCP tools / web studio
  -> submit an approved request
  -> ARC Slurm job produces versioned artifacts
  -> automated checks and human review create approvals
  -> Blender refines approved object candidates
  -> Unreal imports approved packages and runs the physics proof
  -> backend records evidence and produces review
```

Slurm scripts, versioned artifact manifests, Blender automation, and Unreal test harnesses do the actual work. MCP tools make that work discoverable, approval-gated, and inspectable by an instructor or development agent.

## Separate Pipelines That Meet at Unreal

### Scenario pipeline

```text
instructor prompt
  -> ARC LLM job
  -> structured scenario draft JSON
  -> schema and consistency checks
  -> instructor edit / approval
  -> published scenario package
```

Scenarios do not pass through Blender. They remain structured data and do not gain training authority from generation. A generated scenario may become a POC scenario only after an instructor explicitly approves the exact revision.

### Asset pipeline

```text
approved asset request
  -> ARC generation job
  -> candidate mesh, textures, and provenance manifest
  -> automated asset checks
  -> Blender refinement and human review
  -> approved export package
  -> Unreal import and physics configuration
```

Blender is the quality gate for geometry and export readiness. It is not expected to decide scenario meaning or training validity.

## Required Records

Every job and artifact must be traceable. Before connecting a model, define versioned records for:

- **Generation request:** prompt, requester, input references, requested asset roles, model family, and approval status.
- **ARC job:** job ID, account/project, container or environment digest, model version, seed, resources, queue/start/end times, exit status, and log paths.
- **Scenario draft:** schema version, source job ID, deterministic checks, reviewer edits, approval/rejection, and published-package version.
- **Asset manifest:** candidate ID, source job ID, prompt, seed, license or provenance evidence, hashes, dimensions, units, textures, and file paths.
- **Blender review:** reviewer, checklist version, scale/topology/material/collision findings, cleanup steps, export settings, and approval status.
- **Unreal test run:** asset/export version, Unreal and Chaos version, scene configuration, test command, movement/contact observations, result, and logs.

No downstream step may accept an artifact that lacks its upstream approval and provenance record.

## Phased Plan

### Phase 0: Confirm the research boundary

**Purpose:** prevent a technically impressive but unreviewable pipeline.

1. Confirm ARC allocation, project storage, permitted model/container approach, and the supported job-submission method.
2. Select one model path for scenario drafting and one path for asset generation.
3. Decide where Blender runs: local workstation for interactive review first; ARC batch processing only for reproducible non-interactive checks.
4. Confirm that the first Unreal test runs on the local/training-room Windows workstation.

**Exit criteria:** a recorded approved toolchain, storage locations, one named owner for approvals, and no private workaround around institutional access.

### Phase 1: Contracts and artifact layout

**Purpose:** make generated output safe to inspect before generating it.

1. Replace the current mock-only generation-job model with a versioned job contract that can represent queued, running, checking, failed, and review-ready ARC work.
2. Add JSON schemas for scenario drafts, asset manifests, Blender review records, and Unreal physics-test observations.
3. Establish an ignored local artifact workspace plus checked-in sanitized fixtures for tests.
4. Define immutable IDs and hashes from request through Unreal result.
5. Add contract tests, including rejection of missing provenance or skipped approval states.

**Exit criteria:** a local fixture can travel through all record types without an ARC, Blender, or Unreal installation.

### Phase 2: ARC generation runners

**Purpose:** produce real, reproducible candidate artifacts.

1. Add one minimal Slurm job template for structured scenario generation.
2. Add one minimal Slurm job template for chair-candidate generation.
3. Use a pinned Apptainer/container environment and record its digest.
4. Write results only to the approved project workspace, with a job-specific output directory and manifest.
5. Collect resource, queue, duration, error, seed, and model-version evidence.
6. Start with manual job submission and result ingestion; automate only after ARC confirms an approved integration path.

**Exit criteria:** one ARC job generates a structurally valid smoke-room draft and one job produces at least one traceable chair candidate.

### Phase 3: Scenario review and publication

**Purpose:** turn model output into an instructor-owned draft, never automatic scenario truth.

1. Import the real ARC result into the existing Scenario and Asset Studio.
2. Run schema, reference, consistency, and forbidden-content checks.
3. Require edit, approve, or reject from an instructor for the exact revision.
4. Publish only approved content into a versioned POC scenario package.
5. Run it through the deterministic engine and existing replay/review path.

**Exit criteria:** a reviewer can trace an approved POC scenario from its generation request to a replayable backend session.

### Phase 4: Blender refinement and asset approval

**Purpose:** make a generated chair safe enough for a bounded import test.

1. Import one selected candidate into Blender.
2. Verify scale and units, inspect topology and normals, remove obvious artifacts, and establish the origin and orientation.
3. Create or verify render geometry, simple collision geometry, materials, and texture links.
4. Complete the asset review checklist and retain before/after evidence.
5. Export a versioned package, initially FBX or glTF plus a manifest, with a stable naming convention.

**Exit criteria:** one human-approved chair package has documented provenance, correct scale, usable collision geometry, and a reproducible Blender export.

### Phase 5: Unreal import and bounded physics proof

**Purpose:** prove the asset works in an actual physics engine.

1. Create a minimal Unreal Engine 5.8 project: chair, floor, and static contact barrier only.
2. Import the approved package and confirm scale, materials, collision, and physics-asset configuration.
3. Apply the existing versioned chair test configuration: gravity, mass, friction, damping, and one authorized impulse.
4. Record movement, first contact, final transform, elapsed time, and settling state using the shared physics-observation contract.
5. Run the test three times; preserve failure evidence as well as passes.
6. Send observations to the backend for a reviewable result.

**Exit criteria:** the approved chair completes the defined movement/contact proof in three consecutive developer runs, with evidence linked to the asset and configuration versions.

### Phase 6: MCP operator tools

**Purpose:** make the pipeline usable without allowing unbounded automation.

Provide narrow tools such as:

- `generation.request.create` — creates a reviewable request, not a hidden model invocation;
- `generation.job.get` and `generation.job.logs` — report ARC status and sanitized evidence;
- `artifact.manifest.get` — retrieves traceability information;
- `scenario.draft.validate` and `scenario.draft.approve` — preserve the human authority gate;
- `asset.review.record` — records Blender review outcomes;
- `unreal.physics-test.request` and `unreal.physics-test.get` — request and inspect a bounded test, not arbitrary Unreal control.

Tools must not expose credentials, submit arbitrary shell strings, publish unapproved assets/scenarios, or mark a physics result as training validity.

**Exit criteria:** an instructor/developer can inspect each stage and approve or reject transitions through documented, least-privilege operations.

## Verification Matrix

| Stage | Evidence required |
| --- | --- |
| ARC | Job ID, environment digest, seed, model version, resource/timing logs, output hashes |
| Scenario | Schema and consistency report, reviewed revision, approval decision, deterministic replay |
| Blender | Checklist, reviewer decision, source/export hashes, units/scale/collision findings |
| Unreal | Imported asset version, scene/config version, three test-run observations, logs/video if useful |
| End-to-end | One linked record from request to scenario/asset approvals and physics result |

## Explicit Non-goals for This Plan

- autonomous publication of generated scenarios or assets;
- clinical, operational, or training-effectiveness validation;
- generation during an active trainee session;
- full Unreal gameplay, sensing, or projection mapping;
- production deployment or broad multi-user access; and
- an MCP tool that bypasses ARC, Blender, Unreal, or institutional controls.

## First Decision Needed

Approve the Phase 0 boundary and choose the first real generation pair:

1. a smoke-room scenario draft; and
2. a single chair asset for the existing movement/contact proof.

After that decision, the first implementation work is Phase 1 contracts and sanitized fixtures. No ARC job should be submitted until the approved submission method, model path, and artifact storage location are known.
