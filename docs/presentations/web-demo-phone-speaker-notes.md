# Web demo phone speaker notes

These are private notes for the local Scenario Review Console. Keep them on your phone during the meeting. The audience does not need to see them.

## Before the meeting

- Run `python scripts/run_web_demo.py`.
- Open `http://127.0.0.1:8765`.
- Check that the green **Backend online** badge appears.
- Keep the terminal demo ready as a backup: `python scripts/run_menu_demo.py`.
- Increase the text size on your phone so these notes are easy to scan.

## Opening — about 30 seconds

**Say:**

> This is a backend-first proof of concept for adaptive emergency-response training. The larger idea includes AI, Unreal, sensors, and richer simulation. For now, I am focusing on the core loop: the system records an action, updates the scenario, checks a small set of rules, and explains what happened afterward.

**Set the boundary:**

> This is not medical or operational guidance, and it does not measure real trainee skill. Right now, it shows that scenario actions and results can be tracked and reviewed clearly.

## On the path-selection screen

**Point to the four cards.**

> There are two small scenarios. Each one has an expected path and a review path. The review paths try some actions too early, so we can see whether the system explains what went wrong and what changed afterward.

**Point to Backend online.**

> Everything is running locally. The FastAPI backend owns the scenario state, while this webpage presents it in a cleaner way.

## Demo 1 — Smoke room expected path

**Choose Smoke room · expected.**

> I will start with the expected path so the normal flow is easy to follow.

**Click Run selected path. During the 2.5-second pause:**

> This short delay is intentional. It gives everyone a moment to see what was selected before the demo begins.

**While it runs:**

> The page uses friendly labels, but the updates come from the backend and are saved in order.

## On the first review

**Pause here. Do not move on too quickly.**

> This review is the main part of the demo. It shows the final result, the important environmental cues, and anything the POC rules marked for discussion.

**Point to the three totals.**

> These are simple counts from the POC rules. They are not grades, clinical judgments, or real-world performance scores.

**Open Full action sequence only if it helps the discussion.**

> The full sequence is still available, but I keep it closed at first so the audience sees the main story before the technical detail.

## Demo 2 — Smoke room review path

**Click Continue to next path, then run it.**

> This path tries a few actions before the scenario is ready for them. The backend records those findings, allows the scenario to move forward, and accepts a later retry after the missing step is completed.

## Explaining repeated actions

**Point to Why an action was retried.**

> The repeated action is intentional. The first attempt happened too early. Another action changed the scenario state, and the later attempt was accepted. The review explains that story directly, so the audience does not have to interpret field names or raw data.

**Keep the distinction clear:**

> This shows how the software tracks progress. It does not claim to define the correct real-world emergency procedure.

## Hallway paths — optional

If time is short, show the hallway review card and explain that the same review format works for another scenario.

If there is enough time, run both hallway paths with **Continue to next path**.

**Say:**

> The hallway scenario shows that this review structure can work across more than one scenario. It is not limited to the smoke-room example.

## Likely questions

**Is this using AI already?**

> Not yet. The current behavior uses fixed, predictable rules on purpose. AI-assisted adaptation is part of the future vision, but I first want a foundation that is easy to test and review.

**Is this medically or operationally validated?**

> No. These are small POC rules used to demonstrate the software. Real protocol content would need qualified subject-matter experts and a separate validation process.

**Why build the backend first?**

> It gives every future display, including the web page and Unreal, the same source of scenario state, rules, logs, replay, and review.

**Why not start with Unreal?**

> I wanted to prove the scenario logic before spending a lot of time on a polished environment. This gives the visual work a stronger foundation later.

**How far along is it?**

> The POC foundation is around 80 percent complete, and the Dr. Cameron demo is around 90 percent ready. The full long-term vision is still early, at roughly 5 to 10 percent, because AI adaptation, full Unreal work, sensing, physics, deployment, and formal validation are all later phases.

**What comes next?**

> First, I want feedback on whether this review is clear and useful. Then I can finish polishing the demo and move into the smallest useful Unreal display step, while keeping the backend in control of the scenario.

**What does instructor review mean here?**

> The review gives the instructor a clear record for the discussion after a scenario. It shows the actions, important cues, rule findings, retries, and final state. It supports the instructor's review, but it does not grade the trainee or replace professional judgment.

**What should be automated, and what should stay with the instructor?**

> The system can handle consistent tasks such as recording actions, tracking scenario state, finding missing cues, and organizing the session summary. The instructor should decide what those results mean, add context, guide the discussion, and make any real training judgment. The software should provide evidence, not act as the authority.

## If the demo fails

**Say calmly:**

> The local connection interrupted this run, so I am not treating it as a completed result. The main structure is still the same: an action comes in, the backend updates the state, checks the POC rules, saves the log, and creates the review.

Then:

1. Click **Reload local connection**.
2. If needed, restart `python scripts/run_web_demo.py`.
3. Use `python scripts/run_menu_demo.py` as the terminal backup.

## Closing

> The current POC proves a small but complete loop, and it makes that loop understandable after the scenario ends. The feedback I need now is whether the review highlights the right information and whether the progress story is clear.

**Ask:**

> What information would you want to notice first in a post-scenario review?

**Then ask:**

> In a later version, would it be useful for instructors to add their own notes or annotations to a saved review? If so, what format?
