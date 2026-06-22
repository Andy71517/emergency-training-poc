# Future Vertical-Slice Demo Script

This describes the next implementation demo; Sprint 0 does not execute it.

1. Start the local backend with a fresh log directory.
2. Create a session for `smoke_inhalation_room_v0`.
3. Submit `assess_scene` as sequence 1 and display the updated state.
4. Submit an intentionally premature `enter_room` action and display the warning/error without advancing unsafe state.
5. Continue the expected happy path with ordered stub actions.
6. Display the terminal scenario state and next expected actions.
7. Show the client-neutral session response that a future Unreal client could consume.
8. Replay the JSONL log and confirm the same final state and validation outcomes.

Every screen should retain a visible disclaimer: illustrative POC behavior, not clinical or operational guidance.
