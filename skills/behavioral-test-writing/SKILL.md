---
name: behavioral-test-writing
description: Derive behavioral test specifications from groomed work items (Cockburn use cases) — extract requirement-level claims, grade them, rewrite as falsifiable scenarios, and emit Gherkin feature files with a traceability report. Use when asked to write behavior tests, acceptance tests, Gherkin features, or scenario specifications from a groomed issue or story. Not for implementation, unit tests, step definitions, or ungroomed issues — route ungroomed inputs to story-grooming first.
---

# Behavioral Test Writing

Derive behavioral test cases from a **groomed work item** (a Cockburn use case
produced by the story-grooming loop). The work item is the only behavioral
input. Code is never an input: tests derived from code freeze the
implementation's behavior instead of testing the requirements.

## Triggers

- A groomed work item plus a request to derive behavioral tests, acceptance
  tests, or Gherkin features from it.
- A request referencing "behavior specs", "scenario specifications", or
  "executable requirements" for a groomed story.

**Ungroomed input → route back.** If the work item is not groomed — no main
success scenario, no enumerated extensions, open `TBD` placeholders, open
`Qn` questions, or no stakeholder guarantee — do not extract from it. Report
that the item needs grooming first and hand it to the `story-grooming` skill.
Extracting from an ungroomed item reintroduces implementation-shaped claims.

**Out of scope:** step definitions and glue code (this is specification, not
the automation layer); unit/integration test code; reading implementation
sources to "check what the behavior really is".

## Pipeline

Run the five stages in order. Each stage's output feeds the next; the report
(stage 5) is the only externally visible artifact besides the feature file.

### 1. Extract claims

From the groomed use case, extract every requirement-level claim and tag each
with its source element:

- **Scenario claims** — from main success scenario steps: the system response
  the step promises.
- **Extension claims** — from extensions: what the system does when the step
  fails, branches, or is interrupted.
- **Business rule claims** — from BVRs / validation rules: limits, atomicity,
  durability, equivalence, parity.
- **Data claims** — from data requirements: required fields, formats, ranges.
- **Stakeholder guarantee** — the use case's value statement: the observable
  outcome that justifies the story.

**Ignore:** implementation notes, developer-only commentary, plan/task
breakdowns, file or module references, mechanism vocabulary (APIs, storage,
protocols). Claims come from what the use case promises, not how.

### 2. Grade claims

Tag each claim with exactly one grade:

- **Executable** — the claim states an observable outcome under stated
  conditions; it can be shaped into a scenario now.
- **Needs clarification** — the claim is behavioral but underspecified (an
  undefined term, an unstated bound, a missing failure mode). Shape what is
  shapeable and push the rest back as clarification questions (stage 5).
- **Not behavioral** — the claim states intent, constraint on internals, or
  quality attribute without observable conditions. It appears in the report,
  never as a step.

### 3. Rewrite as falsifiable statements

Adapt falsification to specification time: rewrite each executable claim so a
scenario could fail. Per claim shape:

- **Limits** ("at most N", "up to N") → boundary examples at N-1 / N / N+1.
  Each boundary value becomes an example in a `Scenario Outline` (or a
  scenario, if only one boundary is meaningful). Cardinality limits ("at
  most once", "exactly once") are limits where N = 1: the falsifying
  example is a second occurrence.
- **Atomicity / durability** ("all or nothing", "survives restart") → one
  scenario per covered failure mode. Failure modes the claim does not cover
  become clarification questions, not invented scenarios.
- **Equivalence / parity** ("behaves the same as", "treated identically") →
  at least one discriminating fixture per free input dimension — a fixture
  where equivalent inputs must produce equivalent observed outcomes.
- **Extensions** → scenarios whose `Then` states what the **actor observes**
  (message, state, next permitted action), never what the system does
  internally.

A rewrite is falsifiable only if some observable outcome would make it fail.

### 4. Emit

Default format: **Gherkin**. One feature file per work item, named after the
work item's identifier.

Gherkin mapping:

| Use-case element | Gherkin construct |
|---|---|
| Main success scenario | `Scenario` (steps in order) |
| Extensions | failure/branch `Scenario`s |
| BVR limits | `Scenario Outline` with boundary `Examples` |
| Stakeholder guarantee | observable `Then` in the main scenario |

**Pluggable format hook:** everything up to this stage is format-independent
— claims, grades, and falsifiable rewrites are the pipeline's intermediate
model. Only stage 4 is format-specific. A new target format adds an emitter
at this boundary; it never touches stages 1–3.

Hard emission rules:

- `Then` clauses state **observable outcomes only** — no internals, no
  implementation vocabulary. Test each `Then`: *would it still hold if the
  implementation changed?* If not, rewrite or re-grade the claim.
- Every scenario traces to at least one claim; every executable claim traces
  to at least one scenario.
- Non-executable claims never appear as steps.

### 5. Report

Emit a report alongside the feature file containing:

- **Traceability table** — one row per claim: claim id, source use-case
  element, grade, scenario (or "none"), falsifiable statement.
- **Coverage counts** — executable / needs-clarification / not-behavioral
  totals; scenarios emitted; claims with no scenario.
- **Clarification questions** — one numbered question per needs-clarification
  claim with no scenario, phrased so an answer makes the claim shapeable.
  Post these as comments on the work item — the same numbered-question
  convention story-grooming uses (`Q1`, `Q2`, …), numbered in continuation:
  the first question from this skill takes the next free number after the
  item's highest existing `Qn`, and never renumbers existing questions. A
  claim that cannot be shaped into a scenario is a grooming finding:
  the loop closes back to story-grooming, not to invention. Never answer the
  clarification question yourself by inventing a bound or failure mode — the
  claim stays unshaped until the work item answers.

## Worked micro-example

Given a groomed use case with the claim (from a BVR) *"at most 5 items may
be open at once"*:

1. **Extract:** business rule claim, source = the BVR line.
2. **Grade:** executable — observable outcome, stated bound.
3. **Rewrite (falsifiable):** boundary examples 4 / 5 / 6 open items; with 4
   already open, opening one more (the 5th) is accepted; with 5 or 6 already
   open, opening one more is refused.
4. **Emit:**

   ```gherkin
   Scenario Outline: At most 5 items may be open at once
     Given <open_items> items are already open
     When the actor opens one more item
     Then the item is <outcome>

     Examples:
       | open_items | outcome |
       | 4          | opened  |
       | 5          | refused |
       | 6          | refused |
   ```

   (Opening with 5 already open is the 6th attempt and is refused; with 6
   already open the limit is violated before the attempt.)
5. **Report row:** `BR-2 | BVR: open-item limit | executable | scenario
   "At most 5 items open" | 6th open attempt is refused`.

A parallel claim *"the system should feel fast"* grades **not behavioral**
(no observable condition, no bound) and appears only in the report.

## Traceability report columns

| Column | Content |
|---|---|
| Claim id | stable and repo-scoped: feature-file prefix + claim id, e.g. `<feature-file>-SC-n`, `<feature-file>-EXT-n`, `<feature-file>-BR-n`, `<feature-file>-DATA-n`, `<feature-file>-GUAR`. Repo-scoped so the id resolves unambiguously across the multiple reports a repository may hold. |
| Enumeration-id | the use-case element id the claim was extracted from |
| Source element | the use-case line the claim came from (quoted or referenced) |
| Grade | executable / needs clarification / not behavioral |
| Scenario | scenario name, or "none" + reason |
| Falsifiable statement | the observable outcome that would fail |
| Coverage | default empty; set to `review-only` by an operator waiver after review publication |

## Hard rules

- **Groomed inputs only.** Never extract from code, design documents, or
  ungroomed issues.
- **No implementation vocabulary in `Then`.** Observable outcomes only.
- **Traceability is complete both ways** — claim→scenario and
  scenario→claim. An untraced scenario is a manufactured scenario; delete it
  or find its claim.
- **Non-executable claims stay in the report.** Never promote a
  needs-clarification or not-behavioral claim to a step to make coverage look
  complete.
- **Step definitions are out of scope.** Stop at the feature file and report.

`reference/trial-use-case.md` is the synthesized groomed-input fixture for the
manual scenario trial of this skill — input to the trial only, not a real
groomed issue.
