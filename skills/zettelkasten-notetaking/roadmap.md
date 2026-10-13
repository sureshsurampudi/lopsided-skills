# Roadmap — deferred ideas

Not part of the current skill. Unreferenced; revisit deliberately.

1. **Inbox.** Quick capture ("fleeting" notes) separated from ingest. A staging area
   where notes land raw, then go through the full placement + link-search protocol
   later. Guarantees a standing orphan population by design — needs a drain ritual.
   Mikonos's fleeting-note flow also proposes a **combo note** when merging two
   seeds creates a new idea while both sources retain their value. It is unclear
   whether this is useful enough to become a first-class operation; retain it as
   a design reference:
   https://github.com/mikonos/zettelkasten-agent-skills/blob/main/skills/fleeting-note/SKILL.md

2. **Hub / spoke detection.** Structural analysis: find cards with unusually high
   link degree (hubs), sparse regions (spokes/islands). Surfaces where the
   knowledge graph is over-centralized or under-connected.

3. **Tags as implicit links.** (Not from prior discussions.) A tag is a link to a
   virtual parent. Tag co-occurrence would feed the link-search phase. Held off
   deliberately in v1.

4. **Deletion → reorganization.** All children are of value; they were linked to an
   idea that got dropped. Instead of delete-or-promote: **keep the node, mark it
   "obsolete".** The card remains addressable (links don't dangle), its children
   stay in place, but the obsolete marker excludes it from normal discovery and
   signals readers not to build on it. A true delete becomes a rare, manual act.

5. **Re-parenting.** Moving a card (with its subtree) under a better parent when
   the graph reveals one. Placement protocol run in reverse; index and links must
   be updated atomically.

6. **Note states / reliability / stability.** A weight or maturity signal per note
   (e.g., draft → verified → settled). Affects how much trust a reader places in
   the card and possibly whether it can be superseded or re-parented.

7. **Superseding a note.** Effectively delete + insert: the old card is replaced by
   a successor. Has all the problems of deletion (inbound links, children), plus
   the need to point old references at the successor. Probably built on top of
   the "obsolete" state (4) rather than real deletion.

8. **Splitting a note.** One card becomes two; children and links must be
   re-apportioned, and the original id retired or kept as a stub. Refactor-residue
   orphan risk.

9. **ID length growth and between-sibling insertion.** Pure numeric dotted IDs
   (`1.4.7.3.11.2`) get unwieldy in deep branches, and inserting between existing
   siblings forces renumbering. Escape valve: allow letter suffixes at the leaf
   level only, e.g. `1.4.7.3a`, `1.4.7.3b` for insertions. Pragmatic exception,
   not a numbering change.

10. **Document ingestion.** Ingesting an entire document (source code, paper,
    domain material) into notes. Similar in spirit to the research-note-taking
    skill: the user explores a domain and *explicitly* directs the model to
    capture specific things — note-taking is commanded, never automatic.
    Should be built as a separate skill (or command) that *leverages* this
    zettel skill for placement, indexing, and linking rather than duplicating
    that machinery. A sibling skill for fully automatic note capture is
    conceivable later, for future selective re-ingestion, but the v1 ingestion
    flow stays user-directed. Use Mikonos's four-pass ingest protocol (frame →
    tooling → network → completeness), deduplication pass, output contract, and
    QA checklist as a design reference while adapting it to our untyped cards:
    https://github.com/mikonos/zettelkasten-agent-skills/blob/main/skills/literature-note/SKILL.md

11. **Index notes / maps of content.** Curated, short entry-point cards that select
    the best starting notes for a domain, argument structure, or thinking trail;
    they are navigation aids, not exhaustive taxonomies. Traditional
    zettelkasten benefits from these because a large distributed network has no
    obvious front door. Our intended store is a small local second brain whose
    complete title index stays in context and is deliberately kept coherent
    against incremental-edit deterioration, so dedicated index notes may add
    little beyond duplication. Reconsider only when the title index stops being
    a sufficient map or a stable reading path itself becomes valuable. If
    adopted, keep each index selective and add reciprocal links to its entries.
    Design reference:
    https://github.com/mikonos/zettelkasten-agent-skills/blob/main/skills/index-note/SKILL.md

---

## Explicitly rejected (for now)

- **Note kinds.** A note is a note is a note. No typed cards (fleeting vs.
  permanent vs. literature, etc.). Open to revisiting.
- **Meeting/conversation notes.** No dedicated meeting-note operation or schema;
  capture useful ideas through the same note workflow as every other source.
