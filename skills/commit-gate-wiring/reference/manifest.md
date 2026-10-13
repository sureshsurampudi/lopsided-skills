# Gates Manifest

Path: `gates.yaml` at the project root. One file, one manifest, overwritten
in place as gates change — never duplicated per worktree or per plan.

```yaml
# gates.yaml — written by the commit-gate-wiring skill
version: 1
unit_gate:
  command: scripts/test-related.sh   # runs only tests related to changed files
  fallback: npm test                 # used when the wrapper cannot narrow
commit_gate:
  enforced_by: pre-commit            # pre-commit | ci | manual
  command: scripts/no-new-red.sh     # what "run the commit gate" means
  base: merge-base(origin/main)      # what "red vs base" is measured against
extra_gates:
  - name: corpus-invariants
    command: scripts/check-invariants.sh
  - name: golden-diff
    command: scripts/check-golden.sh
  - name: canary
    command: scripts/run-canary.sh
diff_coverage_floor:
  command: scripts/diff-coverage.sh
  threshold: 80                      # percent, over changed lines only
notes: |
  Pre-existing red at base does not block the commit gate.
  diff_coverage_floor is optional; omit the key when not wired.
```

Rules:

- Every listed gate is a single runnable command, verified green and red per
  the skill's Phase 3 before it appears here.
- `enforced_by: manual` means consuming skills must run `command` themselves
  and treat failure as blocking.
- A manifest key without a verified command behind it is worse than an
  omitted key — omit rather than promise.
- Fallback ladder for projects without a manifest: gates declared → run
  them; not declared → say so in the plan or report, and run the test suite
  manually.
