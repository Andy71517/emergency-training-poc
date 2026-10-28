# Unreal editor integration and future trainee client

The filename preserves the original architecture link. Unreal editor automation
now exists; the full trainee client remains future work.

## Implemented editor lane

Unreal 5.8 scripts prepare the reviewed chair, assemble chair room maps, collect
Chaos batch observations and support saved movement recordings. A local file-based
bridge executes fixed backend-created work in the user's open editor. The user
confirmed chair/room/Chaos runs. First live recording and the generic new-furniture
import/collision cooking remain separate acceptance checks.

See [studio guide](../studio-pipeline-runbook.md),
[Unreal folder](../../unreal/README.md) and [current status](../current-status.md).
The binary project is external; Git contains scripts and contracts.

## Trainee session client

The contract in `unreal/contract/` describes an ordered WebSocket client that opens
a session, sends actions and displays backend state/findings. The text/JSON starter
in `unreal/EmergencyTrainingClient/` and `scripts/run_unreal_contract_harness.py`
exercise that boundary. The editor job bridge does not implement it.

The backend owns transitions, validation, end conditions, logs and review. Unreal
may render state and report observations; it must not invent scenario progress or
clinical/operational judgments. Full trainee gameplay, sensing and immersive
training semantics remain future integration work.
