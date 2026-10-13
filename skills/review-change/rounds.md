# Review rounds

A round is one published review of a target. Rounds belong to the **work**, not to a channel: a branch reviewed through its work item and later through its MR keeps counting.

## Markers

`publish-review` writes two hidden markers into every published review, rendered by `scripts/rounds.py marker`:

```
<!-- review-round: round=2 target=pr:144 work=gh:111 base=d53a4d4 head=4437b56 verdict=approve-with-follow-ups -->
<!-- review-decisions: round=2 F1=accept F2=fix U1=file:#146 -->
```

A later comment may carry another `review-decisions` marker for an earlier round (a reversed decision, or an issue number assigned after filing). Per finding ID, the latest marker wins.

Never write markers by hand; never parse them by hand. `rounds.py` owns the format.

## Discovering earlier rounds

Before scoping, run `scripts/rounds.py fetch` on every channel the target has:

| Target | Channels |
| --- | --- |
| MR | the MR; plus its linked work item, if any |
| work item on GitHub/GitLab | the issue |
| work item in beads | the work item (`fetch beads --id`) |

```bash
python3 <skill-directory>/scripts/rounds.py fetch github --repo OWNER/REPO --pr 144
python3 <skill-directory>/scripts/rounds.py fetch beads --id bd-12
```

Merge the results: the round number of this review is the highest `next_round` across channels. If no markers exist anywhere, this is round 1 and the rest of this file does not apply.

**Trust.** On forges, only markers from comments by the operator (default: the authenticated CLI user) count; `fetch` lists any others under `ignored`. Report ignored markers in the review header — someone else posting review markers is worth knowing. Report `problems` (malformed or orphaned markers) under limitations; do not guess what they meant.

## How earlier rounds change this review

Read each earlier round's published comment (the full text, not just the markers) to know what each finding was. Then:

1. **`fix` decisions** — verify each one at the current head. Report the result in the **Prior findings** section of the report: `R1.F1 — resolved` with the evidence, or `R1.F1 — not resolved` with what is still wrong. A `fix` that is not resolved is re-raised as a new finding of this round, citing the earlier ID, at its original severity unless the evidence now supports a different one.
2. **`accept` and `defer` decisions** — do not raise them again. Exception: the code under the finding's anchor changed materially since that round's head (`git diff <round-head>..HEAD -- <anchor paths>`). Then raise a new finding that cites the earlier one and states what changed.
3. **`decline`d unrelated problems** — do not raise them again, under the same exception.
4. **`file`d unrelated problems** — do not raise them again; they are tracked elsewhere.
5. **Findings with no decision** (published before decisions existed, or a marker is missing) — treat as undecided: mention them in Prior findings as `undecided`, and re-raise only if still present.

## Range

Review the full range (merge-base to head) as usual — a later commit can break an earlier one. Also state the **delta since the last round**, `<last_head>..HEAD`, in the header, and spend the falsification effort on it first. If `last_head` is not an ancestor of HEAD (the branch was rebased), say so and use `git range-diff <base>..<last_head> <base>..HEAD` to map earlier commits onto current ones.
