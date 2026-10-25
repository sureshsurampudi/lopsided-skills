# Target: merge request / pull request

An MR may mean a merge request (GitLab) or a pull request (GitHub); the intent is identical.

## Metadata

Query the MR directly with the forge's tooling — `gh` for GitHub, `glab` for GitLab, or the forge's published API — to discover the actual source and target branches, title, description, linked work items, and state. Prefer REST endpoints (`gh api repos/<owner>/<repo>/pulls/<n>`, `glab api projects/:id/merge_requests/<n>`) where a GraphQL-backed command is unavailable.

Do not hardcode or assume any branch name; always derive them from the MR metadata. If either the source or target branch cannot be determined, report the situation as an error and stop.

If the MR body or commits reference a work item (`Refs: #111`, `Closes KEY-12`, `bd-xyz`), the target becomes **MR plus work item**: also read the work item per `work-item.md`, section *Reading the work item*.

## Checkout and range

After `git fetch` (fetch the MR head explicitly if it is not a branch in this repository: `git fetch origin pull/<n>/head` on GitHub, `git fetch origin merge-requests/<n>/head` on GitLab), create the review worktree at the MR head commit (`scripts/worktree.sh create`).

In the review worktree, determine the common ancestor and the change:

```bash
BASE=$(git merge-base origin/<target-branch> HEAD)
git diff $BASE...HEAD
```

Use `git diff -U3` for finding anchors, but trace changed behavior through callers, dependencies, configuration, tests, documentation, and generated artifacts as far as necessary to determine its consequences.

A finding belongs to the MR when the changed code, configuration, data, or contract is a necessary cause of the problem. The defect may manifest in unchanged code.

## Evidence specific to an MR

1. Read its description, commits, merge base, full changed-file diff, and validation claims.
2. Read affected callers, tests, docs, configuration, migrations, and scripts.
3. Determine whether the diff is in scope and whether it changes an established contract.
4. Identify every material claim made by the MR description or changed documentation and trace it to implementation and validation evidence. In the **first review** of a change, map every extracted claim to the claim record — the claim-block comments in the committed test files, keyed by repo-scoped claim id — during evidence gathering; this is the input to the presence check (`method.md`, *Claim-test presence check*). In later reviews, read the claim blocks in the diff's touched test files for review-only residue instead.
5. Read the MR's comments for earlier review rounds — see `rounds.md`.

## Rounds channel

Earlier rounds live in the MR's comments (GitHub: issue comments on the PR; GitLab: MR notes). If the MR links a work item that also carries review markers (a branch reviewed before the MR existed), read those too; rounds continue across both.
