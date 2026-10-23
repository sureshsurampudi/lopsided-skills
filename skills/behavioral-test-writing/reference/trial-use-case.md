# Trial fixture — groomed use case (synthesized)

Synthesized for the unit-004 manual trial of this skill: a self-contained
groomed Cockburn use case standing in for a story-grooming output. Committing
it here keeps the trial reproducible. It is input to the trial only — the
skill itself never reads files from this directory.

## Use case: Reconcile monthly statement

**Actor:** Finance clerk

**Stakeholder guarantee:** the clerk ends the sitting knowing every
discrepancy between the ledger and the bank statement is recorded and
flagged, so nothing is silently absorbed.

**Main success scenario:**

1. Clerk opens the reconciliation for _statement month_.
2. System shows unmatched ledger entries and unmatched statement lines side
   by side.
3. Clerk marks matching pairs; system records each match with the pair and
   the clerk's identity.
4. When no unmatched pairs remain, system marks the reconciliation
   _complete_ and shows the closure summary (matched count, total variance
   zero).

**Extensions:**

- 2a. Statement month already has a completed reconciliation: system shows
  the closure summary read-only and permits no new matches.
- 3a. Marked amounts differ by _variance amount_: system records the match
  as _flagged_ and requires a note before the reconciliation can close.
- 3b. The statement line references an unknown account: system refuses the
  match and shows the account lookup — the clerk resolves or defers the
  line.
- 4a. Clerk closes the session mid-reconciliation: on next open, all
  matches recorded so far are present, in their original state.

**Business rules / BVRs:**

- BR-1: A reconciliation for a given _statement month_ can be completed at
  most once; a completed reconciliation is immutable.
- BR-2: A flagged match must carry a note of at least 20 characters before
  the reconciliation can be marked complete.
- BR-3: A session interrupted at any point preserves every recorded match
  exactly as recorded (all or nothing per match).

**Data requirements:** _statement month_ (YYYY-MM, must be a past month);
_variance amount_ (decimal, two places).

**Implementation notes (to be ignored):** stored in `reconciliation`
table; posting service called via internal RPC; ledger diff computed in a
nightly batch job.
