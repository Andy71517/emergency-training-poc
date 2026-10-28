# Full project vision

This document summarizes the full project goal from `docs/reference/full-project-overview.docx`.

The full project is bigger than the current POC.

The current repo now combines the deterministic foundation with hosted room planning, Blender/Unreal chair workflows and implemented asset automation. See [current status](current-status.md) for evidence and outstanding live checks.

For a side-by-side map of full-system goals, current repo status, open gaps, and safe next experiments, see [full-system-gap-map.md](full-system-gap-map.md).

## North-star goal

The long-term goal is an AI-driven, real-time adaptive emergency-response training platform for firefighters and EMTs.

The full system would combine:

- agentic AI scenario generation
- real-time scenario adaptation
- immersive training environments
- physical mannequins
- multimodal trainee sensing
- structured verification and validation
- cloud-enabled hub-and-spoke deployment
- post-scenario review and continuous improvement

## Full-system loop

At full scale, the intended loop is:

```text
trainee speaks, moves, and performs actions
  -> sensing captures behavior
  -> AI interprets trainee actions
  -> scenario state adapts in real time
  -> validation checks safety and correctness
  -> immersive environment updates
  -> session data is logged
  -> review and learning loop improve future training
```

## Deployment vision

The full project describes a cloud-enabled hub-and-spoke model.

In that future architecture:

- Virginia Tech can act as a regional hub
- pilot spoke sites may include Alexandria Fire Department and the City of Philadelphia
- cloud AI services generate and adapt scenarios
- regional hubs support coordination, caching, resilience, and lower-latency operation
- distributed sites can share consistent training intelligence without each site needing heavy local infrastructure

This is future architecture. The current repo does not implement hub-and-spoke networking.

## AI vision

The full system eventually includes AI and agentic AI that can:

- generate scenario content
- adapt emergency events in real time
- interpret trainee behavior
- update patient state
- update environmental hazards
- support post-scenario review

The room studio calls ARC's hosted model. Description-based SDXL/Hunyuan asset generation is implemented but still needs its first live automated couch run. These authoring/generation paths do not implement validated AI adaptation during a trainee session.

For now, deterministic code stands in for future adaptation so the backend loop can be tested and trusted first.

## Validation vision

The full project includes a verification and validation framework for AI outputs.

In the full system, validation may compare generated patient states, scenario changes, and intervention outcomes against structured sources such as:

- medical dictionaries
- treatment protocols
- dosage guidelines
- expected outcomes
- validated department-provided materials

The current repo does not claim clinical validity or protocol authority.

Current validation means only:

> Did this action follow the rules of this toy deterministic POC scenario?

## Immersive environment vision

The full system may eventually include immersive rooms with:

- multi-projector setups
- projection mapping
- mannequin localization
- projected patient/environment changes
- synchronized audio/visual updates
- physical mannequin integration

The repo has generated-chair evidence, Blender room assembly and Unreal 5.8 scene scripts/Chaos demonstrations. Projection mapping, complete mixed-furniture environments and integrated trainee gameplay remain future work.

## Sensing vision

The full system may eventually observe trainee behavior through:

- voice input
- computer vision
- pose and gesture recognition
- motion tracking
- wearable or environmental sensors
- procedural action detection

The current repo does not implement multimodal sensing.

Manual or scripted trainee actions are used as safe stand-ins.

## Accessibility and scaling vision

The full project aims to support both high-fidelity immersive deployments and lower-cost configurations.

The larger goal is to make advanced training more accessible to departments with different budgets, staffing levels, and locations.

## Relationship to this repo

This repo is not the final platform.

It currently proves the smallest trustworthy software loop:

```text
manual/stubbed action
  -> backend receives event
  -> deterministic scenario engine updates state
  -> POC validation checks rule conformance
  -> client receives state
  -> JSONL log is written
  -> replay/review explains what happened
```

That loop matters because the full system will eventually need the same foundation, even when AI, Unreal, sensing, projection, networking, and richer validation are added later.

## Current build strategy

Because the project is currently being advanced by one solo developer, the full vision is being treated as a north star rather than a single immediate build.

The practical strategy is:

1. prove the backend loop
2. make the session explainable through replay and review
3. make Unreal display backend-owned state
4. add simple visuals only after the display path works
5. review assets manually before trusting generated content
6. validate the new asset/engine lane and mixed rooms, then extend sensing, adaptation, domain validation and deployment through measured checkpoints

This keeps the project realistic without shrinking the long-term goal.

## Important boundary

The full project vision includes future capabilities that are not implemented here yet.

Do not describe the current repo as having:

- validated AI adaptation during active training
- clinical validation
- official EMT/firefighter protocol authority
- hub-and-spoke deployment
- projection mapping
- multimodal sensing
- full Unreal gameplay
- arbitrary automated semantic mesh repair
- calibrated real-world physics or validated training effectiveness
- cloud deployment

The current POC is valuable because it is smaller, testable, replayable, and honest.
