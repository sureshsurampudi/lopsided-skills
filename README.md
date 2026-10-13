# lopsided-skills

A set of agent skills that are highly opinionated, with a dash of NIH thrown in
for fun and profit. They are written in the open
[Agent Skills](https://skills.sh) format (`SKILL.md` with frontmatter), so any
coding agent that reads that format — pi, OpenCode, Claude Code, Codex, Cursor
and friends — can consume them as-is.

All skills here are **GPL-3.0**. See [LICENSE](LICENSE).

## The skills

| Skill | What it does |
|---|---|
| [`plan-work`](skills/plan-work/) | Prepares a controlled code change with strict scope before any implementation — a feature from a groomed story and spec, a bug fix from a bug report, or remediation of review findings. Estimates size first: small changes are solved directly, everything else becomes a right-sized, review-gated plan committed to `.todo`. |
| [`large-task-slicing`](skills/large-task-slicing/) | Breaks large or long-horizon tasks into externally tracked, bite-sized work units with verification gates. One unit at a time, state kept outside the agent's context, so work survives round boundaries and context loss. Includes a `plan.py` state helper. |
| [`zettelkasten-notetaking`](skills/zettelkasten-notetaking/) | Maintains a zettelkasten-style running-notes store for a project: two files, small greppable cards, append-and-place only, with typed link discovery, structural validation, and a `store.py` helper for validation and tooling. Activated by a `.notes/zettel-index.md` signature file. |
| [`review-change`](skills/review-change/) | Read-only review of a merge/pull request, a work item, or both, against code, evidence, contracts and design decisions. Tries to falsify the work's claims and grades findings by a fixed severity and verdict scheme; writes a report file. |
| [`use-case-writing`](skills/use-case-writing/) | Alistair Cockburn use-case format — structure, tree model, extension numbering, result binding, and natural language patterns. |
| [`story-writing`](skills/story-writing/) | Project-specific enrichment of use-case-writing for implementation stories and design documents. Covers delegation syntax, variable styling, and JIRA/Confluence formatting. |
| [`story-designing`](skills/story-designing/) | Design of implementation stories from use cases, feeding story-grooming. |
| [`story-grooming`](skills/story-grooming/) | Grooms issues (epics/stories/tasks) into Cockburn use cases with a fixed architect/product-owner/reviewer split, using the issues themselves as the only communication medium. Supports a continuing groom → review loop across sessions. |
| [`instruction-reliability`](skills/instruction-reliability/) | Techniques for writing effective AI instructions — from scratch or improving existing ones: de-escalating emphasis, fixing skipped or over-applied rules, and making instruction sets consistent. |
| [`worktree-management`](skills/worktree-management/) | Git worktree veneer for parallel development streams — create, attach, list, release. Enforces one plan per root and one root per stream. |
| [`publish-review`](skills/publish-review/) | Publishes a review produced by `review-change` to its channel — PR/MR comment, forge issue comment, or work-item notes — with the operator's decision (fix / accept / defer, file / decline) on every finding. Never reviews code itself. |

`plan-work` and `large-task-slicing` are designed to be used together: the
former decides *what* the controlled change is, the latter drives its execution
unit by unit. `review-change` and `publish-review` are likewise a pair: the
first writes the report, the second posts it. `worktree-management` gives each
parallel stream an isolated root, one plan per root.

## Installation

### Any Agent-Skills-compatible agent (skills.sh)

```sh
npx skills add vhallac/lopsided-skills
npx skills update        # re-sync installed skills later
```

This detects the agents on your machine and installs the skills into the right
locations.

### pi

```sh
pi install git:github.com/vhallac/lopsided-skills
pi update --extensions   # update installed packages later
```

The repo carries a `package.json` with the `pi-package` keyword and a `pi`
manifest pointing at `./skills`, so the pi gallery can also index it.

### Claude Code + OpenCode (local symlink)

Both agents scan `~/.claude/skills/*/SKILL.md`:

```sh
git clone https://github.com/vhallac/lopsided-skills
ln -s "$PWD/lopsided-skills/skills" ~/.claude/skills
```

One symlink feeds both agents; the repo stays the single source of truth.

## Status

Early days: these skills are working drafts in daily use. More will follow in
a proper project structure. Expect churn.

## License

GPL-3.0 — see [LICENSE](LICENSE).
