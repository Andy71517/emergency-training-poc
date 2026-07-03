# Read-through script

This is a spoken version of the meeting deck. It is written to sound natural and beginner-friendly, not corporate.

Target: about 5 minutes of presentation, then 5 minutes of demo.

## Opening

Hey everyone. This project is a proof of concept for a future AI-driven adaptive emergency-response training simulator.

The important thing is that I am not trying to build the whole final simulator in one jump. I am starting with the foundation: can the backend receive an action, update state, check what happened, send the result to a client, log it, and explain it afterward?

That is the core loop I am proving.

## Why I started with the backend

There are a lot of exciting parts in the full project vision: Unreal Engine, generated 3D assets, sensors, physics, AI scenario adaptation, and eventually a much richer training environment.

But if I start with those first, I could build something that looks impressive while the actual truth layer underneath is still unclear.

So I started with the less flashy but more important question:

Can the system keep track of what happened?

That is why this POC is backend-first.

## What the repo proves today

Right now, the local repo can run an end-to-end backend slice.

A manual or stubbed trainee action comes in over WebSocket. The backend validates the message. A deterministic scenario engine updates state from a YAML scenario. A validation layer checks the action against POC rules. Then the backend sends a state update, writes a JSONL log, and the replay/review tools can explain the session later.

That last part is the strongest proof point to me.

The demo is not just saying, "look, the command ran." It can show what actions were taken, what warnings or errors appeared, what the final state was, and whether replay verification passed.

## Current scenario

The current scenario is intentionally tiny. It is a smoke-room software scenario with a wooden chair and an entry door.

The chair may block the path. The door starts closed.

Those details matter because emergency training scenarios should not ignore the environment. Even in this small POC, the room should matter.

If the trainee tries to rush past a blocked path or closed door, the backend can warn or reject that action instead of pretending everything is fine.

To be very clear, this is not real emergency guidance, medical validation, or firefighter protocol authority. It is a toy scenario used to prove the software loop.

## Trust and security boundary

One of the main design choices is that the client is not the source of truth.

A future Unreal client should be able to say, "the trainee wants to attempt this action." But the backend decides what actually happened.

The backend owns the state change, validation result, final outcome, log entry, replay result, and review summary.

I also added a small POC security baseline. It rejects strange IDs, unsafe message shapes, oversized payloads, wrong sequence numbers, and duplicate event IDs.

That is not production security yet. There is no authentication, TLS, cloud hardening, or real data handling policy. But it sets the right direction early.

## Where Unreal and assets fit later

Unreal is still future work, and I am keeping it that way for now.

The future Unreal side should first be a simple display client. It connects, sends actions, receives backend-owned state, and shows that state clearly. Text/debug display first, real scene later.

Generated assets are also future work. If I use tools like Hunyuan 3D later, those assets should go through Blender/manual review before I trust them in the project.

For now, the chair and door are scenario objects and metadata, not meshes and not real physics.

## What comes next

The next careful steps are to keep tightening the display contract, keep improving review summaries, add richer object metadata, and eventually test a tiny Unreal display.

After that, it starts making more sense to bring in Blender, generated assets, and eventually physics.

The order matters:

First prove the loop.

Then make it visible.

Then make it immersive.

One monster at a time.

## Demo transition

For the demo, I would run:

```powershell
python scripts/run_local_demo.py
```

I would show the happy path, the warning/error path, the replay verification, and the review summary.

The main thing I want Dr. Cameron to see is that the backend can keep track of what happened, explain it afterward, and leave room for the bigger simulator pieces later.
