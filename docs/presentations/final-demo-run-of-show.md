# Final demo run-of-show

Use this as the main guide during the Dr. Cameron demo. It is built for a calm 7-minute presentation, followed by questions.

The main route uses two smoke-room paths:

1. the expected path shows the normal scenario flow
2. the review path shows an early attempt, a state change, and a later retry

The hallway scenario is optional. It is there to prove that the review format works across more than one scenario, but it does not need to be run unless there is time or interest.

## Main message

> The current POC proves a small, trusted loop: an action is recorded, the backend updates the scenario, deterministic rules check it, and the system creates a clear review afterward.

## Before anyone joins

- Run `python scripts/run_web_demo.py`.
- Open `http://127.0.0.1:8765`.
- Confirm that **Backend online** is green.
- Select **Smoke room · expected**, but do not start it yet.
- Keep `docs/presentations/web-demo-phone-speaker-notes.md` open on your phone.
- Keep a second terminal ready for `python scripts/run_menu_demo.py` if needed.
- Close unrelated windows and silence notifications.
- Do not open Unreal unless it has already been tested and there is a clear reason to show it.

## Seven-minute run

| Time | Screen and action | What to say |
|---|---|---|
| 0:00–0:40 | Show the Scenario Review Console. Do not click yet. | “This is a backend-first proof of concept for adaptive emergency-response training. The larger vision includes AI, Unreal, sensors, and richer simulation. Today I am showing the core loop underneath that vision.” |
| 0:40–1:10 | Point to **Backend online** and the four path cards. | “Everything here is running locally. The backend owns the scenario state, and this webpage presents it clearly. There are two small scenarios, each with an expected path and a review path.” |
| 1:10–1:25 | Keep the selection screen visible. | “This is not medical or operational guidance, and it does not measure real trainee skill. These are deterministic POC rules used to demonstrate the software.” |
| 1:25–1:40 | Click **Run selected path** for Smoke room · expected. | “I will start with the expected path so the normal flow is easy to follow. The short pause gives everyone a moment to see what was selected.” |
| 1:40–2:10 | Let the path run. Point briefly to the progress state. | “Each action updates backend-owned state and is saved in order. The friendly labels are only the presentation layer.” |
| 2:10–3:10 | Stop talking for a moment when the review appears. Then point to the result, totals, and important cues. | “This review is the main proof point. It shows what happened, the important environmental cues, and anything the POC rules marked for discussion. These counts are not grades or real-world performance scores.” |
| 3:10–3:25 | Leave **Full action sequence** closed. | “The detailed sequence is available for traceability, but I keep it closed at first so the main story comes before the raw detail.” |
| 3:25–3:40 | Click **Continue to next path**, then **Run selected path**. | “The review path now tries a few actions before the scenario is ready for them.” |
| 3:40–4:15 | Let the review path run. | “The backend records the finding, allows the scenario to move forward, and can accept a later retry after the missing state has changed.” |
| 4:15–5:20 | On the review, point to **Why an action was retried**, then the discussion points. | “The repeated action is intentional. The first attempt happened too early. Another action changed the scenario state, and the later attempt was accepted. The system explains that relationship directly instead of making the audience decode raw fields.” |
| 5:20–5:40 | Keep the review visible. | “This shows software state progression. It does not claim to define the correct real-world emergency procedure.” |
| 5:40–6:20 | Point back to the overall review. | “For an instructor, this creates a clear record for the discussion after a scenario: actions, cues, findings, retries, and final state. It supports professional judgment; it does not replace it.” |
| 6:20–7:00 | Stop clicking. Face the audience if possible. | “The software can consistently record and organize evidence. The instructor should decide what it means and guide the discussion. What information would you want to notice first in a post-scenario review?” |

## Follow-up question

After Dr. Cameron answers the first review question, ask:

> In a later version, would it be useful for instructors to add their own notes or annotations to a saved review? If so, what format would be most useful?

Do not suggest the fields yourself unless she asks. The likely direction is a combination of structured fields and free-form notes, but the content should come from instructor and subject-matter-expert feedback.

## If you have two extra minutes

Show the hallway cards without running both paths.

Say:

> The hallway scenario uses the same review structure. That helps show that the system is not limited to one hardcoded smoke-room example.

Run one hallway path only if Dr. Cameron asks to see the second scenario.

## Four-minute version

If time is cut short:

1. Give the 30-second opening and boundary.
2. Run **Smoke room · review** only.
3. Show the final result, important cues, and retry explanation.
4. Explain instructor review in one sentence.
5. Ask the main feedback question.

Short instructor-review line:

> The system organizes the evidence; the instructor provides the meaning and judgment.

## If someone interrupts with a question

- Answer briefly.
- Return with: “Coming back to the review…”
- Continue from the next row instead of restarting your explanation.
- If the discussion is useful, skip the hallway scenario and protect the closing question.

## If the webpage fails

Say:

> The local connection interrupted this run, so I am not treating it as a completed result. The underlying flow is still action, backend state update, POC rule check, saved log, replay, and review.

Then:

1. Click **Reload local connection** once.
2. If it does not recover quickly, move to `python scripts/run_menu_demo.py`.
3. Run the smoke-room expected or review path from the terminal.
4. Do not spend meeting time debugging.

## If a difficult scope question comes up

Use one of these short answers:

**Is this AI already?**

> Not yet. The current rules are fixed and predictable on purpose. AI-assisted adaptation is future work.

**Is this validated emergency guidance?**

> No. It is a software proof of concept. Real protocol content would require qualified experts and a separate validation process.

**Why backend first?**

> It gives the web page and any future Unreal client one traceable source of scenario state, logs, replay, and review.

**How far along is it?**

> The POC foundation is around 80 percent complete, and the Dr. Cameron demo is around 90 percent ready. The full long-term vision is still early, at roughly 5 to 10 percent.

## Final closing

If the conversation needs a closing statement, use:

> The current POC proves a small but complete loop and makes that loop understandable afterward. My next decision should come from whether this review shows instructors the right information.

## After the meeting

Write down:

- the first review information Dr. Cameron looked for
- whether she preferred structured fields, free-form notes, or both
- any wording or screen element that caused confusion
- which future feature she cared about most
- the smallest next change supported by her feedback

Do not promise a new feature during the meeting. Capture the feedback first, then choose the next realistic slice.
