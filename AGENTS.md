# lopsided-skills — AGENTS.md

This repository develops agent skills and their support scripts. Skills are
verified by manual scenario runs; scripts under `skills/*/scripts/` are
ordinary tested code.

## Scope

- Deliverables are `SKILL.md` files and their support scripts under `skills/`
  (e.g. `large-task-slicing/scripts/plan.py`, `zettelkasten-notetaking/scripts/store.py`).
- A skill's "requirement" is observable agent behavior, not document structure.

## Skill testing

- Skills are tested ONLY by manual invocation: a fresh agent round, given a
  pinned scenario, must exhibit the required behavior.
- This carve-out applies to skill behavior only. Automated tests DO apply to
  support scripts, which are ordinary code (see Verification).
- Record the scenario and expected behavior in the story/task that drives the
  change; verification is that scenario run manually.

## Verification

- For a skill change, verification is the manual scenario run, reported in the
  completion report. Do not substitute "file written" for verification.
- Helper scripts (e.g. `plan.py`, `store.py`) are ordinary code and follow the
  full methodology, including tests.

## Changes

- Skill behavior changes are routed through `plan-work` / `large-task-slicing`
  like any other change.
- Keep skills self-contained; lightly reference other skills, never replicate
  them.
- Use `instruction-reliability` when writing or revising skill instructions.
