# Validation

Validation in this repo means one narrow thing: checking an action against explicit POC rules.

It does not establish clinical correctness, safe real-world practice, or EMT/firefighter protocol authority.

The validator returns structured `ok`, `warning`, or `error` results. If a rule blocks a transition, the scenario state should stay unchanged, but the attempted action still gets logged for review.

Each scenario has its own rule file under `validation/rules/`.

Current rule files:

- `smoke_inhalation_room_v0_rules.yaml`
- `blocked_exit_hallway_v0_rules.yaml`

These rule files are deterministic POC fixtures. They are not clinical validation, official emergency guidance, or certification scoring.
