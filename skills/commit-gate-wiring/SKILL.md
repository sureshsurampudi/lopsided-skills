---
name: commit-gate-wiring
description: Install and wire commit/verification gates into a project that has automated tests — a unit gate (test-related wrapper), a pre-commit "no new red vs base" gate, promoted invariant/golden-diff/canary checks, and an optional diff-coverage floor. Writes a gates manifest that plan-work, large-task-slicing, and review-change read. Use when a project reaches the point of having automated tests and its gates are still undeclared or ad-hoc. Refuses when the project has no automated tests yet — there is nothing to wire.
---

# Commit Gate Wiring

This skill installs declared verification gates into a project and records
them in a machine-readable manifest. Its output is consumed by other skills:

- **plan-work** reads the manifest to decide whether the commit gate is
  enforced by a hook or must be run manually before proposing merge.
- **large-task-slicing** reads the manifest to fill each slice's `verify`
  command instead of guessing project-specific checks.
- **review-change** reads the manifest to re-run gates as falsification
  evidence.

## Trigger and refusal

Activate when the project has automated tests and at least one of:

- no declared gates (no CI test step, no pre-commit hook, no manifest), or
- gates exist but are ad-hoc (commands in someone's head or in chat logs).

**Refuse** when the project has no automated tests. Before that point there is
nothing to wrap, gate, or floor. Say exactly that and stop — do not scaffold
tests as a side effect of wiring gates.

## Files in this skill

| File | Read when |
| --- | --- |
| `SKILL.md` | always — detection, install, verification, manifest format |
| `reference/manifest.md` | before writing the gates manifest |

## Phase 1 — Detect

Inspect the project root only (read-only):

1. **Test runner.** Look for package scripts / Makefile / justfile targets
   that run tests. Record the base test command.
2. **Relatedness.** Does the runner support filtering tests by changed files
   (e.g. `jest --findRelatedTests`, `go test ./...` with package paths,
   `pytest` with node-id selection)? If not natively, is a wrapper script
   feasible without heroics?
3. **Git hooks.** Is there a hooks directory in use (`.git/hooks` active,
   husky, pre-commit framework, `core.hooksPath`)?
4. **CI config.** Any pipeline file that runs tests? Record its invocation.
5. **Existing checks.** Invariant scripts, golden files, canary/deployment
   entry points that a previous session used as "anchor checks" without
   declaring them.

Record findings in prose. Do not change anything yet.

## Phase 2 — Install gates

Each gate is optional; install the ones detection supports. Order matters:
the unit gate feeds the commit gate.

1. **Unit gate — test-related wrapper.** A script that runs only tests
   related to the changed files (diff against merge-base). If the runner has
   native relatedness, the script is a thin wrapper; otherwise fall back to
   the full suite and say so in the manifest.
2. **Commit gate — pre-commit "no new red vs base".** A pre-commit hook that
   runs the unit gate and fails when a test that was green at the merge-base
   is red in the working tree. Pre-existing red tests (red at base) do not
   block the commit; they are listed, not failed. If the project uses a hook
   framework, install through it; if not, a plain script under
   `.git/hooks/pre-commit` (or the configured hooksPath) is acceptable —
   note in the manifest that the hook is local-only until the framework or
   CI adopts it.
3. **Promoted anchor checks.** If detection found invariant scripts, golden
   diffs, or a runnable canary, promote each into a declared gate with a
   fixed command instead of leaving it project-specific folklore.
4. **Diff-coverage floor (optional).** If coverage tooling exists, wire a
   floor over the changed lines only. Do not impose a whole-codebase
   coverage gate as part of wiring; that is a project decision, not a
   skill default.
5. **CI adoption.** Where a CI pipeline exists, mirror the commit gate there
   so the gate is enforced for all authors, not just locally.

Keep every gate a single command. A gate that needs explanation to run is a
document, not a gate.

## Phase 3 — Verify each gate

A wired gate that has never blocked anything is decoration. For each gate:

1. Run it on a green tree — must pass.
2. Deliberately introduce a red change (e.g. flip an assertion), run the
   gate — must fail with an identifiable message.
3. Revert the red change; confirm the tree is green again.

Record all three outcomes. A gate that fails step 1 or passes step 2 is not
installed — fix or drop it and say which.

## Phase 4 — Write the manifest

Write the gates manifest per `reference/manifest.md` at the project root.
The manifest is the contract between this skill and the consuming skills:
plan-work, large-task-slicing, and review-change read the manifest, never
re-derive gates from detection. If no gate could be installed, say so in the
plan instead of writing an empty manifest and pointing at it as if gates
exist.

Finish with a short report: which gates are wired, which were refused and
why, and the fallback ladder from `reference/manifest.md` for sessions in
projects without the manifest.
