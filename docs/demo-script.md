# Demo Script

Use this flow to show the POC without overselling it.

1. Start the local backend.
2. Open a session for `smoke_inhalation_room_v0`.
3. Send `assess_scene` as the first action.
4. Show the returned state update.
5. Send an intentionally wrong action, like entering the room too early.
6. Show the backend warning or error and confirm the state did not advance incorrectly.
7. Run the happy path in order.
8. Show the terminal scenario state.
9. Show the JSONL log.
10. Replay or summarize the log to prove the session can be reviewed later.

Keep the disclaimer visible in any demo: this is illustrative POC behavior, not clinical or operational guidance.
