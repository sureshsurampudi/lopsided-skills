# 010 — The persistent claim record is the committed behavioral-test-writing traceability report

**Status:** accepted (amended 2026-10-23)

## Context

Issue #31 adds a claim-test presence check to `review-change`: every new claim
in a first review must map to a test/scenario, else the verdict is blocked
(operator waiver is the only unblock, leaving `coverage: review-only` residue).
For later reviews to flag PRs touching review-only claim code, `review-change`
needs a stable, read-only place to locate claim records and their coverage
status. Plan assumption A-1 (issue #31 plan, units 3 and 4) proposed the
mechanism without evidence at plan time.

## Decision

The persistent claim record is the behavioral-test-writing traceability
report, **committed in the repository next to the emitted feature files**.
`review-change` performs a **read-only lookup** on it during review, keyed on
the repo-scoped claim id + enumeration-id (so the id resolves unambiguously
across the multiple reports a repository may hold). The record is never
modified during review: the `coverage: review-only` waiver residue is written
by the **operator after review publication**, not by the reviewer.
No separate claim-record store is introduced.

## Consequences

- Later reviews detect unverified-behavior changes by reading the committed
  record next to the feature files; no extra tooling or index.
- If a domain has no committed traceability report, every new claim is
  treated as unmapped — the presence check applies with no special case.
- The assumption was validated by the issue #31 manual scenario trial
  (2026-10-23): a committed `CLAIM-RECORD.md` with stable claim ids was
  located and updated through the full presence-check → waiver → residue
  path (steps a–d of the trial).
- Amended 2026-10-23 (PR !37 review R1.F1/R1.F2): mapping key is the
  repo-scoped claim id + enumeration-id per the extended report schema;
  review-time access to the record is read-only — the reviewer never writes
  a claim row, and the `coverage: review-only` waiver write is the
  operator's post-publication step. The record-location choice itself is
  unchanged.
