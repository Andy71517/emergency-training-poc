# Full-system gap map

Reviewed October 28, 2026. This map distinguishes working baselines, implemented
paths needing acceptance and future research. [Evidence](current-status.md),
[roadmap](roadmap.md), [full vision](full-project-vision.md).

| Goal | Current implementation/evidence | Remaining gap and next check |
| --- | --- | --- |
| Natural-language rooms | Hosted ARC planning, seeded chair layouts, saved packages; user-confirmed live workflow | Mixed-asset resolution, footprints and bindings; broader scenario semantics |
| Text-described furniture | SDXL reference -> Hunyuan shape/paint -> retrieved model; frontend dispatch/recovery implemented | First live automated couch/SDXL run after SSH and remote checkout setup |
| Editable prepared assets | Real Blender MCP cleanup/CoACD/export verified on a synthetic fixture | Actual couch quality, collision fit and human review; arbitrary semantic repair remains unsolved |
| Unreal furniture import | Generic FBX/UCX/material importer and package preflight | First actual engine import/cooking/material and contact checks |
| Generated chair baseline | Real ARC chair shape/paint, accepted Blender repair/19 hulls, user-confirmed Unreal demo | Broader asset-quality/physics validation; no automatic approval for new designs |
| Complete editable environments | Blender chair rooms and Unreal per-room maps; user-confirmed assembly | Mixed-furniture end-to-end Blender/Unreal environment generation |
| Real physics | Browser primitive Rapier proof; user-confirmed bounded Unreal chair/Chaos room runs | Calibrated measurements, contact/fit validation and training relevance |
| Visual recordings | Engine capture protocol, FFmpeg encoding/retry and saved downloads implemented | First live Unreal screenshot/MP4 validation; no browser live stream |
| Interactive training sessions | Two deterministic toy scenarios, ordered actions, state/rule/log/review loop | Integrated immersive trainee client and domain-reviewed content |
| AI scenario authoring | Real room planner plus separate legacy fixture draft/edit/approve module | Room plans are not approved executable training scenarios; connect publication and runtime semantics |
| Adaptive scenarios | Deterministic transitions and seeded variation | Validated AI adaptation during a session, uncertainty and controlled changes |
| Trainee interpretation/sensing | Manual/scripted/user-clicked actions | Voice/pose/sensor adapters, confidence, privacy and independent evaluation |
| Patient/mannequin integration | Toy occupant state only | Medical model, localization, hardware integration and domain validation |
| Hazard simulation/navigation | Layout cues and aisle/exit constraints | Fire/smoke/heat models, agents/navigation and evacuation validity |
| Review and learning | Replayable JSONL, instructor discussion summaries, persistent spatial evidence | Expert annotations, approved evaluation methodology and learning feedback loop |
| Projection mapping | Future architecture notes | Hardware, calibration, localization and physical safety validation |
| Hosting/hub-and-spoke | Local single-user app; CS Launch/ARC/workstation split documented | Institutional deployment/access agreement, auth/roles, TLS, resilience and multi-site sync |
| Production security | Bounded messages/packages, scoped artifacts, verified SSH and fixed workers | Multi-user authorization, quotas, retention, audit and operational hardening |

## Evidence rule

Configured access is not a successful connection. A saved request is not a submitted
job. A submitted job is not a returned model. A prepared package is not an accepted
engine import. Engine motion is not calibrated physics or clinical training validity.
Keep those states distinct in documentation and the user interface.

## Next complete slice

Run and inspect one actual couch through the automated lane, validate the prepared
package in Unreal, then extend reviewed mixed-furniture room contracts and both
assemblers together. Preserve the working chair and deterministic session baselines.
