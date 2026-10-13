# Feature design profile

Input: a groomed story (use case) plus a detailed high-level spec. The end
result — and sometimes the steps to it — is given.

## Refine the input; do not re-engineer the codebase

The plan's product is the decomposition and verification, not the solution
prose.

- Decompose the given end result by behavior/outcome, never by file/module.
- Reconnaissance is bounded to step 1's size estimation and confirming named
  assumptions ("confirm assumption X about Y"). Record what you confirm in
  findings.
- MUST NOT pre-identify every changed line or file-level edit set in the plan —
  the plan outlives the reconnaissance that produced it, and a line-level map
  both goes stale and role-plays precision it does not have. Where a unit needs
  code mapping, that mapping is the unit's own first action at execution time.
- If you already know the solution: state it once as `Solution hypothesis:` in
  the scope lock, then still produce the unit decomposition and verifications.
  Do not invent deliberation you did not do. If the whole change qualifies for
  step 1's small gate, say so and use that path instead of writing a design.

## Contracts likely touched

Name interfaces and standing contracts from the spec's vocabulary (the user's
terms), not from code reading. Flag any long-standing contract or user-visible
behavior as an open question — those are the user's decisions to make.

## Shape

These tasks finish in one or two sittings: a single-level unit list, no
milestone hierarchy. Default order: shared contracts/foundations first, then
behavior slices, then integration and final verification.
