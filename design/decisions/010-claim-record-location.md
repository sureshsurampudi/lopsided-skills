# 010 — The persistent claim record is the committed behavioral-test-writing traceability report

**Status:** accepted

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
`review-change` reads and updates it by claim-id (read-only lookup for
detection; the waiver writes `coverage: review-only` to the claim-id row).
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
