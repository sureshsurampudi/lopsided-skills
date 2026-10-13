# Bugfix profile

Input: a bug report (symptom, expected, actual) or review findings highlighting
shortcomings.

## Bug reports arrive pre-validated

The user reproduces a bug before accepting it. When a report reaches this
workflow, treat it as valid and confirmed — reproduction is not a step here,
because it would re-run the user's acceptance gate, not advance the fix. Start
at locate.

## Locate (bounded)

Find the defect site and the blast radius:

- Log candidates and evidence to findings as you go
  (`Tried: ... → Result: ...`).
- Never retry a failed approach — change the approach (large-task-slicing
  rule).
- Stop when the defect site is identified and the blast radius is named. If
  the cause is still unclear after bounded effort, log findings and ask rather
  than ranging further.

## Minimal-fix scope lock

- In scope: the smallest change that fixes the symptom.
- Must not change: everything observable beyond the symptom — behavior, APIs,
  output shape.
- Regression guard: the check that fails before the fix and passes after.
- Bug class: misread spec | collateral | other — record it in the PR or issue
  comment, not `findings.md` (`.todo` archives are not committed).

For review findings: one unit per finding (or per tightly-coupled finding
group), each carrying its regression guard where cheaply expressible. If the
user wants the fixes reported back (e.g. PR comments), make that a final unit:
one short entry per fix — finding reference plus one-line approach, no
walkthrough.

## Verification

Prefer a regression test that captures the failure mode as the unit's verify
command — when it is cheaply expressible. It verifies the fix; it is not an
acceptance gate for the report. If expressing the failure as a test is
expensive, verify with the affected tests plus the full suite and label the
verification weak in the report.

For collateral bugs, prefer a boundary check (corpus invariant, golden or
differential output, contract snapshot) as the regression guard when it
generalises beyond the single failure. Use a unit test when it does not.
