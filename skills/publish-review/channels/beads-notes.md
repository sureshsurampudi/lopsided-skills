# Channel: beads work-item notes

For a work item tracked only in beads (no PR/MR, no forge issue). The review is appended to the work item's notes, so it travels with the work item in the repository.

## Appending

Notes are a single field: writing them replaces them. Appending must therefore keep everything already there.

1. Read the current notes: `bd show <id> --json` (or the installed version's equivalent; check `bd show --help`). Save them to a scratch file.
2. Append a separator line (`---`) and the rendered review to that scratch copy.
3. Write the whole result back with the installed version's notes option (check `bd update --help`; commonly `bd update <id> --notes "$(cat <file>)"`).
4. Re-read the notes and confirm the earlier content is unchanged and the new review is present. If the earlier content changed in any way, restore it from the scratch copy immediately and report the failure.

If the installed `bd` has no way to set notes, stop and report it; do not fall back to another field without the operator's say-so.

## Verifying

`rounds.py fetch beads --id <id>`: this round must appear with its head and decisions. Beads is local, so there is no author filter: anyone who can write the work item can write markers. That is acceptable for a single-operator repository; say so if the repository is shared.

## Size

Long notes are fine, but keep the Minor and Observation detail blocks inside `<details>` as on forges; the notes are read in a terminal as often as rendered.
