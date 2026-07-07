# Dr. Cameron review rubric

This rubric is for reviewing the current POC as a project milestone.

It is not a trainee grading tool. It is not clinical validation. It is not firefighter or EMT protocol scoring.

The goal is simpler:

> Can I show that the backend foundation is real, explainable, and ready for the next careful step?

## How to use this

Use this after running the local demo:

```powershell
python scripts/run_local_demo.py
```

For each category, score the current demo from 0 to 3.

| Score | Meaning |
| --- | --- |
| 0 | Not shown yet |
| 1 | Present, but rough or unclear |
| 2 | Working clearly enough for this POC |
| 3 | Strong enough to guide the next project decision |

The most important thing is not getting all 3s.

The important thing is knowing what is proven, what is still rough, and what should come next.

## POC review rubric

| Area | What Dr. Cameron should be able to see | Evidence in the demo | Current target |
| --- | --- | --- | --- |
| Backend loop | A trainee action travels through the backend and changes state. | WebSocket action messages produce state updates. | 2 |
| Determinism | The same ordered actions produce the same state. | Replay verifies the JSONL log. | 2 |
| Review usefulness | The system explains what happened afterward. | Post-scenario review shows action timeline, final state, warnings, errors, and takeaways. | 2-3 |
| Environmental awareness | The scenario tracks simple cues instead of only counting actions. | Room scan, chair, door, smoke/visibility, communication, monitoring, exit path, and occupant search are visible in review. | 2 |
| Warning/error clarity | Skipped cues are explained in beginner-friendly language. | Warning/error findings include instructor notes. | 2 |
| Scope honesty | The demo does not pretend to be a real emergency training authority. | Review and docs repeat that validation is POC rule checking only. | 3 |
| Backend as source of truth | The client sends actions, but the backend owns state and validation. | Unreal/debug contract only displays backend-owned state. | 2 |
| Logging and replay | The session can be inspected after the fact. | JSONL logs can be replayed and summarized. | 2 |
| Security baseline | The local backend treats client messages as untrusted. | ID checks, sequence checks, duplicate event checks, payload limits, and session limits are in place. | 2 |
| Path to full system | The work clearly connects to the larger project vision. | Roadmap separates current POC from AI, Unreal, sensing, projection, and deployment. | 2 |

## What a strong current demo should communicate

A strong demo does not need fancy graphics yet.

It should make these points obvious:

- I can send a trainee action into the backend.
- The backend updates a scenario state.
- The backend notices simple environment cues.
- The backend flags skipped steps with plain explanations.
- The session is logged.
- Replay can verify what happened.
- The review can explain the run afterward.
- Unreal, AI, sensing, assets, and physics are future layers, not current claims.

## Review questions to ask after the demo

These are good Dr. Cameron-facing questions.

- Was the action-to-state loop clear?
- Was the review summary easy to understand?
- Did the warning/error path explain skipped cues clearly?
- Did the scope feel honest?
- Did the demo make the future full-system direction more believable?
- What part felt most worth improving next?

## Scope-control rubric: what I avoided and why

This section is part of the review because restraint is a project decision too.

Avoiding a feature right now does not mean the feature is unimportant. It means the current foundation is not ready to carry it safely yet.

| Avoided for now | Why I avoided it | What should be true before adding it |
| --- | --- | --- |
| Real AI or LLM calls | AI would make the system harder to test before the state loop is trusted. | Message contracts, replay, review, and deterministic baselines are stable. |
| Clinical or protocol authority | The repo should not claim medical/firefighter correctness without validated sources and expert review. | There is an approved validation source process and domain review workflow. |
| Real trainee sensing | Voice, camera, pose, and sensor input add privacy, uncertainty, and data-handling issues. | There is a clear consent/data plan and a safe adapter interface. |
| Full Unreal scene | A scene can look impressive while hiding weak backend logic. | The backend contract and text debug display are stable. |
| Generated 3D assets | Generated assets need review for scale, geometry, licensing, and safety before use. | A Blender/manual review checklist exists and one object pipeline is tested. |
| Real physics | Physics needs a real engine, collision setup, mass, gravity, and careful testing. | Object contracts define the needed metadata and Unreal can display backend state. |
| Projection mapping | Projection needs hardware, calibration, tracking, and safety planning. | A basic Unreal/display layer works first. |
| Mannequin integration | Physical integration adds hardware, tracking, and procedure-detection complexity. | The software state model can represent patient/mannequin state cleanly. |
| Hub-and-spoke networking | Distributed deployment adds cloud, latency, resilience, and security concerns. | Local sessions, auth, logging, and trust boundaries are stronger. |
| Production security/auth | Production security is a whole layer, not a quick checkbox. | The project has real users, data policies, auth needs, and deployment targets. |
| Real scoring/certification | Scoring can imply authority the POC does not have. | Evaluation criteria are reviewed with domain experts and tied to validated training goals. |

## The main takeaway

The current POC should be judged as a foundation.

The best outcome is not:

> This already looks like the final simulator.

The better outcome is:

> This proves the backend can track a training situation, explain what happened, and give future AI, Unreal, sensing, and validation layers a trustworthy place to connect.

