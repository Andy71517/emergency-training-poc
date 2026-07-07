# Read-through script

This is a spoken version of the shorter meeting deck.

Use it to practice the story, not to read word-for-word. The tone should be clear, prepared, and a little casual.

Target: about 7 minutes of presentation plus demo.

## Opening

Hey everyone. This is a progress update on the emergency training simulator proof of concept.

The full idea is much bigger than the repo currently is. The long-term goal is an adaptive emergency-response training simulator where a trainee can act, the environment can respond, and an instructor can review what happened afterward.

Eventually, that larger system could involve Unreal Engine, AI scenario adaptation, generated or reviewed 3D assets, sensors, physical props or mannequins, validation frameworks, and larger deployment models.

But that is a huge ask for one person. So I am treating the full project as the north star and building toward it through checkpoints.

## Why I narrowed the first slice

The first useful question was not, "Can I build the final simulator right away?"

The first useful question was:

Can the system keep the truth straight?

In other words, if a trainee action comes in, can the backend record it, update scenario state, check whether it fits the toy scenario rules, send the state to a client, log the event, and explain the session afterward?

That is why I started backend-first.

If that loop is unclear, then Unreal, AI, physics, assets, and sensors could make the project look more impressive while hiding a weak foundation.

## How I am keeping it buildable

Because this is a solo-dev project right now, I am cutting it into thin slices.

Each slice should prove one idea, stay demoable, and make the next slice easier.

That is the reason I delayed the expensive tools at first. Unreal, generated assets, physics, sensing, and AI all matter eventually, but they need a clear job before I pull them into the build.

So the strategy is not to lower the ambition. It is to make the ambition buildable.

## Sprint 0 and the first backend loop

Sprint 0 created the repo skeleton: docs, architecture notes, ADRs, schemas, toy scenarios, validation rules, backend folders, scripts, logs, Unreal placeholders, and asset pipeline notes.

After that, I implemented the first working backend loop.

A manual or scripted trainee action comes in over WebSocket. The backend validates the message. A deterministic scenario engine updates state from YAML. The validation layer checks POC rule conformance. Then the backend sends a state update, writes a JSONL log, and replay/review tools can inspect the session afterward.

That made the repo executable, not just planned.

## Review became the proof point

As the project evolved, the strongest thing became the review summary.

The demo is not just "the command ran."

The system can show the action timeline, final state, warnings, errors, replay verification, environmental cue status, and plain-English reviewer notes.

That matters because training is not only about what happens during the scenario. It is also about what the instructor can understand afterward.

## Scenarios and environmental cues

The first scenario is a small smoke-room software scenario.

It includes smoke and visibility cues, a wooden chair that may block the path, an entry door that starts closed, occupant visibility, communication, scanning, and environmental monitoring.

Then I added a second deterministic scenario: a blocked-exit hallway with a hallway obstacle, exit-door state, and monitoring cue.

These are not real emergency procedures. They are toy scenarios used to prove that the backend can track environmental cues and flag ignored cues.

The second scenario also helps prove that the engine is not hardcoded to one room.

## Unreal so far

Unreal is starting carefully.

The first Unreal goal is not a full scene. It is just a display client.

The hardcoded debug panel is visible. The repo has a JSON-to-debug-text bridge, which turns backend-shaped display JSON into a simple text file that Unreal can show.

The next step is making Unreal read that text file automatically. After that, Unreal can parse JSON directly. After that, it can connect to the backend WebSocket.

The key boundary is that Unreal displays backend-owned state. It does not become the simulator brain.

## Current checkpoint and timeline

Right now, the repo can run a full local backend loop.

It has a FastAPI WebSocket backend, deterministic YAML scenarios, POC validation rules, JSONL logs, replay and review summaries, a one-command local demo, and the first Unreal display path.

The near-term checkpoints are:

First, make Unreal read the generated debug text file.

Second, make Unreal parse the display JSON.

Third, connect Unreal to the backend WebSocket so the panel can update from live backend state.

After that, the mid-term work is a simple Unreal scene shell, clearer object display, Blender/manual asset review, and a few reviewed placeholder assets.

Later, once the foundation is stable, it makes more sense to explore generated assets, real physics, sensing, AI-assisted adaptation, stronger validation, and deployment planning.

## What I am not claiming

I want to be careful about the boundary.

This repo does not have real AI calls yet. It does not claim clinical validation. It does not claim firefighter or EMT protocol authority. It does not simulate real physics. It does not generate 3D assets. It does not implement multimodal sensing, projection mapping, cloud deployment, or a full Unreal scene.

That is intentional.

The current foundation is small enough to test and honest enough to build on.

## Demo transition

For the demo, I would run:

```powershell
python scripts/run_local_demo.py
```

I would show the happy path, the warning/error path, the replay verification, and the review summary.

The main thing I want Dr. Melissa Cameron to see is that the backend can track what happened and explain it afterward.

If Unreal is ready, I would also show the debug panel, but I would frame that as the first display-client step, not the full simulator.

## Feedback ask

The feedback I would want is:

Does the review summary feel useful from an instructor point of view?

Are the environmental cues understandable?

Does the backend-first order make sense?

Is the scope controlled enough for a solo developer?

And what should the next scenario emphasize?

## Closing

The project started as a large full-system vision.

It is evolving into checkpoints that I can build, test, show, and improve.

The order I am following is:

First prove the loop.

Then make it visible.

Then make it immersive.

One monster at a time.
