# Funding-Proof Platform Plan

## Why the project is expanding

The deterministic POC proved that actions can change backend-owned scenario state, produce explainable findings, and create a saved instructor review.

Dr. Cameron's funding feedback identified the next two capabilities that need stronger evidence:

1. AI-assisted generation of interactive scenario drafts for immersive training rooms.
2. AI-assisted generation of scenario assets that can later be imported into Unreal and participate in physics.

This is an expansion of the working foundation, not a replacement for it. The deterministic scenarios remain the baseline for testing, replay, comparison, and safe demonstrations.

## Three-platform split

Each platform should do the work it is best suited for.

### CS Launch: application and control plane

CS Launch is the preferred future home for long-running web services:

- React instructor and developer interface
- FastAPI application
- generation request and job metadata
- authentication, secrets, and database services when those are approved
- stable web access for project users

CS Launch should track and present generation work. It should not be assumed to have the same GPU capacity as ARC.

### VT ARC: AI generation plane

VT ARC is the preferred home for expensive, queued compute:

- scenario-model experiments
- structured scenario generation
- reference-image and 3D-asset generation
- Blender cleanup and automated asset checks
- reproducible model comparisons and benchmarks

ARC jobs should use Slurm and reproducible containers such as Apptainer. Interactive GPU sessions are useful for setup and debugging; repeatable generation and benchmarks should move to batch jobs.

### Local or training-room workstation: immersive runtime

The Windows workstation remains the preferred home for:

- Unreal Engine
- scene assembly and rendering
- Chaos collision and physics
- trainee interaction
- room-specific visualization and hardware integration later

AI may propose or generate an object's geometry, textures, and metadata. Unreal's physics engine applies gravity, collision, mass, friction, and forces. These are related parts of the pipeline, but they are not the same job.

## Intended workflow

```text
instructor prompt
  -> AI creates a structured scenario draft on ARC
  -> schema and consistency checks run
  -> instructor reviews, edits, approves, or rejects the draft
  -> backend publishes an approved scenario package
  -> asset manifest requests required objects
  -> ARC generates candidate assets and processing results
  -> automated checks and human review approve selected assets
  -> Unreal imports approved assets and configures collision and physics
  -> trainee interacts with the scenario
  -> backend records state, findings, and the instructor review
```

Human approval is a required boundary. Generated output does not become an approved training scenario or asset merely because a model produced it.

## Frontend direction

The current web review console should grow into a small **Scenario and Asset Studio**. It should reuse the existing visual style and review components instead of being replaced.

The eventual interface can have these focused areas:

- **Scenarios:** enter an instructor prompt and review generated drafts.
- **Generation jobs:** see queued, running, checking, failed, and review-ready work.
- **Assets:** inspect previews, provenance, dimensions, materials, validation results, and Unreal import status.
- **Sessions:** use the existing action history and instructor-review experience.
- **Developer Lab:** reproduce jobs with model versions and seeds, compare results, and inspect technical logs.
- **System:** show the health of the web application, ARC connection, storage, and Unreal handoff.

The trainee's immersive experience belongs primarily in Unreal. The current user-controlled web path remains useful as a developer test harness, accessible fallback, and remote demonstration of backend behavior.

The approved visual-proof direction is hybrid: build a browser-based 3D physics preview first, then reproduce the bounded proof in Unreal Engine 5.8. Both clients should use the same backend-owned semantic contract. See [visual-physics-proof.md](visual-physics-proof.md).

## First implementation slice

Before connecting a real model, build one mocked end-to-end authoring flow:

1. Define a versioned generated-scenario draft schema.
2. Define a generation-job record with status, timestamps, model label, seed, and errors.
3. Add an instructor prompt form to the local React app.
4. Simulate visible job progress locally.
5. Display a structured draft that can be approved or rejected.
6. Keep the existing deterministic engine and scenarios unchanged.

This slice tests whether the workflow makes sense to Dr. Cameron before ARC access, model selection, networking, and GPU costs complicate it.

## First compute experiment

After ARC access and an approved submission method exist, run a narrow vertical slice:

- generate a smoke-room scenario draft from a prompt
- produce an asset manifest containing one leather chair
- generate candidate chair assets
- process and inspect one candidate in Blender
- import the approved candidate into Unreal
- configure basic collision and Chaos physics
- record generation time, processing time, GPU type, GPU memory, failures, and manual cleanup effort

The first target is generation before a session or during room preparation. Generation during active trainee interaction is a later research target and must not be described as real-time until it has been measured.

## Integration boundary still to confirm

CS Launch and ARC are both Virginia Tech resources, but that does not automatically mean a CS Launch service may submit Slurm jobs directly.

The approved connection might use a restricted service account, SSH, a gateway, an API, or a manual handoff. Until ARC and CS staff confirm the supported method, use manual job submission and result ingestion for experiments. Do not build a private workaround around institutional access controls.

## Success evidence

The funding proof should report measurements rather than broad claims:

- scenario generation duration
- asset generation and cleanup duration
- GPU model, count, memory use, and queue time
- schema-validation pass and failure counts
- number of regeneration attempts
- manual review and cleanup time
- Unreal import success
- collision and physics setup result
- whether the same seed and model version reproduce a comparable result

These measurements show feasibility. They do not establish clinical validity, protocol authority, training effectiveness, or operational readiness.
