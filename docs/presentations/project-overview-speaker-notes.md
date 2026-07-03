# Speaker notes

These notes match `project-overview-slides.md`.

The slide deck is intentionally light. The notes carry the explanation so the slides can breathe.

Tone: clear, beginner-friendly, and confident. This should feel like an on-campus project update for Dr. Cameron first, with a little pitch-deck polish second.

## 1. Emergency Training Simulator POC

Open by saying this is a proof of concept for a larger adaptive emergency-response training simulator.

Set the boundary right away: this is not the final system, not operational guidance, and not clinical validation. It is the backend foundation.

Suggested line:

> I am not trying to build the entire simulator in one jump. I am proving the loop that the simulator would need underneath it.

## 2. The short version

Explain the whole project in one plain sentence.

The current repo proves that an action can enter the backend, update scenario state, get checked, reach a client-facing message, and leave a reviewable log.

This is the first thing worth trusting before adding Unreal, AI, assets, sensing, or physics.

## 3. Why this project exists

Frame training as a feedback problem.

A simulator is not useful only because it looks realistic. It becomes useful when the trainee can act, the environment can respond, and the instructor can review what happened.

That review piece is why replay and logs are central.

## 4. The trap I am avoiding

This is where the talk can be casually honest.

It would be easy to start with the exciting tools: Unreal, Hunyuan 3D, Blender, sensors, physics, AI calls. But if the backend cannot keep state cleanly, all that visual polish hides a weak foundation.

Suggested line:

> I want the shiny parts eventually. I just do not want them hiding the truth layer.

## 5. The core loop

Walk through the loop slowly.

Manual or stubbed trainee action enters the backend. The deterministic scenario engine updates state. The validation layer checks whether the action fits the toy scenario rules. The client gets the state update. The event gets logged. Replay and review explain the session later.

This is the heartbeat of the repo.

## 6. What works now

This is the progress slide.

Keep it grounded:

- it runs locally
- it uses FastAPI and WebSockets
- the scenario engine is deterministic
- validation is POC rule checking
- logs are JSONL
- replay/review turns logs into explanation
- the local demo ties it together

Avoid sounding like it is production-ready.

## 7. Current demo scenario

Explain the scenario as a tiny software test.

The smoke-room scenario is deliberately small. The wooden chair can block the path, and the entry door starts closed. The purpose is to prove environmental cues can affect state and validation.

Repeat the boundary: this is not real firefighting, EMT, or medical guidance.

## 8. Why the chair and door matter

This slide explains why the objects are not random.

The chair and door prove that the room can matter. A future simulator should not ignore obvious environmental cues.

Right now these objects are backend state and metadata only. Later, richer fields can support collision, mass, force direction, gravity notes, and Unreal display behavior.

## 9. The strongest proof point

This is the key slide for Dr. Cameron.

Do not say only "the demo ran." Say the system can explain what happened afterward.

The review summary shows actions, final state, warnings, errors, replay verification, and environment cue status. That is the beginning of instructor-facing value.

## 10. Trust boundary

Explain the trust boundary in normal language.

The client can request an action. The backend decides whether the action changes state, whether it creates a warning or error, whether the scenario ends, and what gets logged.

This matters later because Unreal should not become the source of truth.

## 11. Security baseline

Clarify that this is small POC hardening.

The backend rejects unsafe or messy inputs like strange IDs, unexpected fields, oversized payloads, wrong sequence numbers, and duplicate event IDs.

Then name what is not here yet: authentication, authorization, TLS, cloud deployment, production rate limiting, and real data policy.

## 12. Future Unreal role

Unreal should have a boring first job.

It should connect, send simple actions, receive backend state, and display that state clearly. Text/debug display comes before real scenes or gameplay.

Suggested line:

> I want Unreal to become a good display client before it becomes a giant second source of logic.

## 13. Submission packet vs meeting deck

Explain the repo cleanup.

The submission packet is for reading/submission. The deck is for talking live. The demo is for proof. The docs are for deeper context.

This keeps each artifact from trying to do every job at once.

## 14. Next useful steps

Use this as a roadmap slide.

The next work should strengthen the future display contract, improve review output, enrich environment object metadata, then test a tiny Unreal display. Blender and generated assets come later, and real physics comes after the object model is stable.

## 15. Demo plan

Move from slides to terminal.

Run:

```powershell
python scripts/run_local_demo.py
```

Point out:

- backend detected or started
- happy path
- warning/error path
- replay verification
- review summary
- chair/door cue status

## 16. Closing

End with the project order.

First prove the loop. Then make it visible. Then make it immersive.

The closer can be:

> One monster at a time.
