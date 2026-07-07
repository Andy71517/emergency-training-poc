# Full-system gap map

This map connects the original project overview to the current repo.

The short version:

> The current POC is not the full emergency-response training platform yet. It is the backend foundation that future AI, Unreal, sensing, validation, deployment, and asset work can connect to safely.

## How to read this

Each row compares:

- what the full project eventually wants
- what exists in the repo right now
- what is still missing
- the safest next experiment

This is useful for Dr. Cameron because it shows the project is moving toward the larger vision without pretending the POC is already the final system.

## Gap map

| Full project goal | Current repo status | Main gap | Safest next experiment |
| --- | --- | --- | --- |
| AI-generated scenarios | Not implemented. The repo uses deterministic YAML scenarios. | No real model calls, no generated scenarios, no agentic planning. | Keep deterministic baselines, then test AI-generated scenario drafts offline before any live integration. |
| Real-time scenario adaptation | Partly simulated through deterministic state transitions across checked-in scenarios. | No AI-driven adaptation, uncertainty, or dynamic branching beyond checked-in rules. | Compare the smoke-room and blocked-exit hallway scenarios, then add controlled branching only when review stays clear. |
| Trainee action interpretation | Manual or scripted actions only. | No voice, camera, pose, object detection, or procedural inference. | Define a future sensing adapter contract before using real sensors. |
| Multimodal sensing | Not implemented. | No audio/video capture, wearable input, sensor confidence, privacy plan, or data policy. | Write a sensing boundary doc and start with fake/stubbed sensor messages only. |
| Immersive Unreal environment | Contract and text-display preview only. | No real Unreal scene, room, gameplay, lighting, smoke, or interaction. | Build a text-only Unreal debug display that reads backend-owned state. |
| Projection mapping | Not implemented. | No projectors, calibration, tracking, room mapping, or hardware safety plan. | Wait until Unreal can display state clearly, then document projection requirements. |
| Physical mannequin integration | Not implemented. | No mannequin state model, localization, tracking, or procedure detection. | Add a simple `mannequin_state` concept as metadata before touching hardware. |
| Patient state changes | Minimal POC occupant state only. | No vitals, symptoms, responsiveness, injury model, or medical validation. | Add non-clinical toy patient-state fields only after the validation boundary is clearer. |
| Environmental hazards | Simple backend cues only: chair, door, visibility, communication, monitoring, exit path, hallway obstacle, and exit door. | No real fire/smoke behavior, heat model, physics, or hazard simulation. | Add more deterministic environmental cues before real simulation. |
| Verification and validation framework | POC rule-conformance only. | No validated clinical/protocol references, no domain-reviewed scoring, no AI-output validation. | Define a source-review workflow with Dr. Cameron before adding real validation material. |
| Post-scenario review | Working POC review and replay summary. | Needs more instructor examples, comparison views, and clearer reviewer workflow. | Improve review summaries and add more demo cases. |
| Continuous learning loop | Logs are written and replayed, but not used for learning. | No model improvement, analytics, or feedback loop yet. | Keep logs explainable first; later define what data could safely feed improvement. |
| Hub-and-spoke deployment | Documented only as future architecture. | No cloud, regional hub, spoke sites, caching, failover, or distributed sync. | Stay local until auth, logging, state contracts, and deployment needs are clearer. |
| Centralized instructor support | Review docs exist, but no instructor dashboard. | No live instructor UI, session controls, multi-site supervision, or role model. | Start with an instructor/reviewer checklist and later a simple review dashboard concept. |
| Accessibility and tiered deployment | Mentioned in docs only. | No low-cost deployment profiles or hardware tiers. | Draft high-fidelity, medium, and low-cost configuration profiles later. |
| Generated assets | Placeholder pipeline only. | No Hunyuan 3D outputs, Blender review, licensing review, or Unreal import. | Write the Blender/manual review checklist before generating assets. |
| Real physics | Metadata preview only. | No gravity, collision, mass, tipping, force, or physics engine behavior. | Define object metadata needs, then test one reviewed object in Unreal later. |
| Production security | Small local POC guardrails only. | No auth, TLS, user roles, real rate limiting, cloud hardening, or data governance. | Keep local security boundaries documented; add production security only when deployment becomes real. |

## What is already proven

The repo already proves the foundation loop:

```text
manual or scripted action
  -> backend receives event
  -> deterministic scenario state changes
  -> validation checks POC rule conformance
  -> client-ready state is produced
  -> JSONL log is written
  -> replay and review explain what happened
```

That foundation matters because every future layer needs a trusted state trail.

If AI adapts a scenario later, the backend still needs to know what changed.

If Unreal displays a room later, it still needs backend-owned state.

If sensors detect trainee behavior later, those detections still need to become checked events.

If validation becomes more serious later, the system still needs a clear log and review path.

## What is intentionally postponed

These parts are important, but they are not safe to add first:

- real AI calls
- clinical or protocol validation
- generated 3D assets
- real physics
- full Unreal gameplay
- projection mapping
- multimodal sensing
- mannequin integration
- hub-and-spoke networking
- cloud deployment
- production authentication
- real trainee scoring

The reason is simple: each one adds complexity and credibility risk.

The current POC is strongest when it proves the trusted backend loop first.

## Safest build order from here

The next steps should stay small:

1. Add this gap map. Done.
2. Add a second deterministic scenario. Done.
3. Build a text-only Unreal debug display.
4. Add the Blender/manual asset review checklist.
5. Only then begin tiny experiments with generated assets or richer Unreal display.

This order keeps the project understandable.

It also makes the demo stronger because every future feature has a clear reason to exist.

## Meeting framing for Dr. Cameron

A useful way to explain this:

> The original project overview describes the full destination. This repo is the first foundation layer. The gap map shows what exists today, what is missing, and what the safest next experiment should be for each future capability.

Another useful version:

> I am not trying to make the POC look bigger than it is. I am trying to make sure every next feature connects cleanly to the larger system.

## Main takeaway

The current repo does not yet contain the full AI-driven simulator.

It does contain the first piece that the full simulator will need:

> an explainable backend state loop with logs, replay, validation boundaries, and review.
