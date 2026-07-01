# UX principles

These are simple design rules for future client and review work.

## 1. Show state clearly

The user should be able to tell what is happening without reading raw JSON.

Current examples:

- scenario phase
- chair moved or not moved
- door open or closed
- warnings and errors

## 2. Keep the backend as the source of truth

The UI should display backend state.

It should not invent scenario state on its own.

## 3. Make warnings useful, not dramatic

Warnings should explain what happened in the POC.

They should not shame the trainee or pretend to be official emergency guidance.

## 4. Keep the review readable

The review should be clear enough for a human to understand quickly.

A good review should answer:

- What happened?
- What changed?
- What was warned?
- What was blocked?
- Did replay confirm the run?

## 5. Avoid visual complexity too early

Do not build polished UI before the contract is stable.

Text output and simple debug panels are enough for now.

## 6. Use honest labels

Use labels like:

- POC rule check
- preview metadata
- future physics candidate
- local demo

Avoid labels that imply production readiness, real medical authority, or real emergency certification.

