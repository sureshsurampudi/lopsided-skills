# 010 — The persistent claim record lives in the repository (claim blocks in committed test files)

**Status:** accepted (amended 2026-10-23, amended 2026-10-25)

## Context

Issue #31 adds a claim-test presence check to `review-change`: every new claim
in a first review must map to a test/scenario, else the verdict is blocked
(operator waiver is the only unblock, leaving `coverage: review-only` residue).
For later reviews to flag PRs touching review-only claim code, `review-change`
needs a stable, read-only place to locate claim records and their coverage
status. Plan assumption A-1 (issue #31 plan, units 3 and 4) proposed the
mechanism without evidence at plan time.

## Decision

**Amended 2026-10-25 (issue #45):** the persistent claim record is the
**claim-block comments in the committed test files** that verify the claims —
no longer the committed behavioral-test-writing traceability report. The
`.todo/specs/<work-item>.feature` scratchpad stays planning-only and is never
committed; during implementation, each claim that has a test is emitted from
the scratchpad as a claim block (comment on the test carrying the stable
repo-scoped claim id, claim text, and Gherkin scenario text). Claims without
a test are not emitted and are not durable — they are review-scope-only. The
read-only-at-review and operator-writes-residue rules below are retained
unchanged; coverage/waiver residue now lives with the test-side comment.

**Original decision (2026-10-23):** the persistent claim record was the
behavioral-test-writing traceability report, **committed in the repository
next to the emitted feature files**.
`review-change` performs a **read-only lookup** on it during review, keyed on
the repo-scoped claim id + enumeration-id (so the id resolves unambiguously
across the multiple reports a repository may hold). The record is never
modified during review: the `coverage: review-only` waiver residue is written
by the **operator after review publication**, not by the reviewer.
No separate claim-record store is introduced.

## Consequences

- Later reviews detect unverified-behavior changes by reading the committed
  claim record — since the 2026-10-25 amendment, the claim blocks in the
  committed test files; no extra tooling or index.
- If a domain has no committed claim record, every new claim is
  treated as unmapped — the presence check applies with no special case.
- The assumption was validated by the issue #31 manual scenario trial
  (2026-10-23): a committed `CLAIM-RECORD.md` with stable claim ids was
  located and updated through the full presence-check → waiver → residue
  path (steps a–d of the trial).
- Amended 2026-10-23 (PR !37 review R1.F1/R1.F2): mapping key is the
  repo-scoped claim id + enumeration-id per the extended report schema;
  review-time access to the record is read-only — the reviewer never writes
  a claim row, and the `coverage: review-only` waiver write is the
  operator's post-publication step. The record-location choice itself was
  at that point unchanged.
- Amended 2026-10-25 (issue #45): the record location moves from the
  committed traceability report to claim-block comments in committed test
  files. This is a continuation of the same record-location question, not a
  supersede — the mapping key, the read-only-at-review rule, and the
  operator-writes-residue rule carry over. A claim's committed test is its
  record, keyed by the claim id; the report is no longer the durable store.
