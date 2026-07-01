# Validation

Validation in this repo means one narrow thing: checking an action against explicit POC rules.

It does not establish clinical correctness, safe real-world practice, or EMT/firefighter protocol authority.

The validator returns structured `ok`, `warning`, or `error` results. If a rule blocks a transition, the scenario state should stay unchanged, but the attempted action still gets logged for review.
