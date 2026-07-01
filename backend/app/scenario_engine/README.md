# Scenario Engine

The scenario engine loads YAML scenario files and applies state changes.

It is deterministic: the same scenario version, previous state, and ordered action should always produce the same next state. That keeps tests and replay simple.

It does not decide whether a real-world action is correct. It only follows the toy scenario data.
