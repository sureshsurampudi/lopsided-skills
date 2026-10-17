# Development Methodology Requirements

Version: 1.4

Status: revised requirements for the `emergent-contract-coding` skill and its supporting scripts. Supersedes v1.3. The previously generated `SKILL.md` is not authoritative and should be regenerated from this document.

Changes from v1.3, in brief:
- Interface direction (input/output/internal) is distinct from change authority (rigid/lax); these are independent classifications.
- A missing capability may prompt merge consideration but does not itself satisfy the merge test.
- A recorded `leave` applies to a structural candidate actually considered, not every pair that does not merge.

Changes inherited from v1.3:
- Plain vocabulary throughout; coined terms replaced with definitions (section 2).
- "Flow" is the program implementing one input interface; "behavior" is what a specification requires of it.
- Structure decisions reduced to merge, divorce and leave. Promotion is folded into merge. Depth surgery, vertical merges, unrolling and recursive restructuring are out of scope.
- The merge test is defined operationally: same transformation, co-changed, cause not excluded. Excluded causes are listed.
- Script requirements added (section 4).
- Requirements renumbered. Card IDs in brackets are traceability anchors to the source notes and are not used in the skill text.

## 1. What is being built

1. **A prose skill named `emergent-contract-coding`** that guides an LLM agent through writing and changing code. Each work item runs a write loop: contract walk, write the flow, structure pass. The structure pass keeps call sites consistent and makes the only structural decisions: merge, divorce or leave.
2. **Deterministic scripts** that generate and check the interface-usage registry and maintain the decision and knowledge logs without drift.
3. **An isolated-context skill**, specific to each agent environment, that runs a task in a fresh context and returns only its result. For pi, this means running pi as a subprocess with provider and model selection. Other agents define their own. The methodology skill depends on this capability but does not define it.

The substrate in the target repository:
- `registry.md`: generated and checked by scripts, never edited by the agent.
- `decision-log.md`: append-only and load-bearing.
- `knowledge-log.md`: append-only and advisory.

## 2. Terms

**Interface.** A contract: signature, results, error results and side effects.

**Input interface.** An interface invoked by an external entity to trigger a flow, such as a REST endpoint, an event handler or a CLI command.

**Output interface.** An interface invoked by the application to hand a flow or effect to an external entity, such as publishing a message through a Kafka client library.

**Rigid interface.** An interface whose contract is outside the project's control, such as a third-party library contract or a system owned by someone else. It can be changed only through a request to its owner, never by writing code.

**Lax interface.** A contract whose change authority belongs to the project and which may be changed under the rules in this document. It may be created or reshaped through a merge.

**Interface classification.** Direction and change authority are independent attributes. Direction identifies an interface as input, output or internal; change authority identifies it as rigid or lax. For example, an externally specified input contract may be both input and rigid. Do not treat these attributes as mutually exclusive categories.

**Behavior.** What the program must do in response to one input interface, as defined by a specification: the main scenario plus its error results.

**Flow.** The program that implements one behavior: one input interface, implemented by calling output interfaces and lax interfaces.

**Call site.** A (calling implementation, called interface) pair. The calling implementation is a flow or a lax interface's implementation, identified by file plus function/symbol. This identifier is stable under ordinary edits but may change under refactoring.

**Siblings.** Call sites of the same interface.

**Co-change.** The same change needed in two or more places within one work item.

**Work item.** One specification implemented or changed, ending in one commit.

**Operator.** The human supervising the agent.

**Pause.** Stop the work item and ask the operator. This prototype is attended, so there is no unattended fallback.

**Bug echo.** The same kind of defect fixed in one flow and later in another.

## 3. Requirements

### Units and scope

- **R1 — One behavior, one flow, one function.** A flow implements one input interface's behavior in a single function: main scenario plus error results, written as explicit return paths. The test count is not prescribed. [14.16.1.1, 14.8, 14.16.1.12]
- **R2 — Extraction is earned, duplication is the default.** Extract a block into its own function or lax interface only when it earns a name in the flow's narrative or becomes a useful test seam. When a second flow needs the same logic, duplicate it. Whether the copies merge is decided later by the merge test (R16), which keeps co-change visible. [14.16.1.2]

### Substrate

- **R3 — The registry is generated, never hand-edited.** `registry.md` maps each interface to its call sites and records its direction (input, output or internal) separately from its change authority (rigid or lax). An interface may have one value on each axis, such as an input interface that is also rigid. The agent changes the registry only by running the scripts (section 4). Calls the scripts cannot resolve are listed as unresolved, never treated as absent. [14.4, 14.16.1.5]
- **R4 — The decision log is append-only, and every entry carries a reason.** Entries are never edited or deleted; a later entry supersedes or resolves an earlier one. Each entry has a date, a work-item reference, a kind, the affected interfaces/call sites, the decision and a reason. Entry kinds:
  - `merge`, `divorce`, `leave`: structure decisions (R15);
  - `divergence`: call sites wanted different changes to one interface (R14);
  - `wish-declined`: a missing capability deliberately not added (R10);
  - `fix`: a confirmed defect fixed;
  - `bug-echo`: a fix that repeats the kind of an earlier fix in another flow;
  - `drift`: the registry differed from the code in a way that mattered;
  - `unresolved`: a relevance, impact or cause question escalated to the operator, and its later resolution.

  [14.10, 14.16.2, 15.13]
- **R5 — The knowledge log is advisory.** `knowledge-log.md` records, for people, the reasoning behind merges and deliberate non-merges: date, interfaces, outcome, rationale and work-item reference. The agent must not use it as evidence for structure decisions.

### Write loop

- **R6 — Walk the contracts before writing.** The specification names its input interface and the output interfaces it must reach. Starting from those outputs, walk backwards through the interfaces that lead to them, collecting contracts only, never bodies. The result is the relevant interface set and the call order between those interfaces. Run the walk in an isolated context through the agent's isolated-context skill, so implementation bodies don't enter the writing context. How to compose a route from the set is left to the agent. [14.16.1.3]
- **R7 — A contract too thin to judge fails loudly.** If a contract does not state enough to judge fit, flag it for repair or deliberately inspect the body, and record which. Never judge suitability from an interface's name. [14.16.1.3, 14.16.1.4]
- **R8 — Reuse requires whole-contract fit.** Reuse an existing lax interface only when its whole contract fits the need: results, error results and side effects together. Resemblance of names or code is not evidence of fit. When nothing fits, call the output interfaces directly. [14.16.1.6]
- **R9 — Write one linear function, check-then-act.** Validate everything before the first external call that changes anything. Keep external effects late. Return error outcomes inline. Call other flows only through their interfaces. [14.16.1.12]
- **R10 — When an interface lacks a needed capability.** Handle the wish in this order: [14.16.1.13, 14.3]
  1. Ask whether the wish is evidence that the flow and that interface should be merged. Record it as a candidate for consideration in the structure pass; the wish alone does not satisfy the merge test (R16). Any merge happens only through the structure pass.
  2. For a lax interface, the change goes through the interface-change check (R14).
  3. For a rigid interface, never change its contract. A wrapper or caller-side workaround is acceptable only if it achieves the need through the rigid interface's existing contract with the required semantics. Otherwise, pause: the change belongs to the owner's request path. Never present a new wrapper as solving a capability the rigid interface lacks.
  4. Record a declined wish once as `wish-declined`, so it isn't re-argued at every later write.

### Structure pass — ends every work item

- **R11 — Pass sequence.** After the flow is written:
  1. Regenerate and check the registry.
  2. List every call site of every interface the change affected.
  3. Give each relevant call site an outcome (R12), propagating caller updates as needed (R13).
  4. Run the interface-change check wherever an existing interface must change (R14).
  5. Run the merge test on observed co-change (R16).
  6. Record the decisions.

  [14.16.1.21]
- **R12 — Every relevant call site gets an explicit outcome.** First decide whether the call site is relevant to the change. Each relevant call site is updated, left unchanged with a recorded reason, or paused for the operator with an `unresolved` entry. Uncertainty is never resolved by silence. [14.16.1.22, 15.8]
- **R13 — Caller updates propagate until stable, within ownership.** If an update affects further callers, repeat R12 for them until no further update is needed. The boundary is ownership, not file location: rigid interfaces and systems owned by others are outside it, while input interfaces owned by this project stay inside. Pause if a propagated change would alter externally visible behavior. Structural decisions do not recurse: the pass does not re-examine an interface it created or merged during the same pass. [14.16.1.23, 14.16.1.24]
- **R14 — Interface-change check: a disagreement test, not a likeness test.** For each existing interface the change must alter: [14.16.1.25]
  - Rigid: never changed. Apply R10.
  - Lax, all call sites want the same change: change it in place and update every caller in the same work item.
  - Lax, call sites want different things: create a new interface for the new need, leave the old one serving its callers, and record a `divergence` entry.

### Merge, divorce, leave

- **R15 — Only three structure decisions, made only in the structure pass.**
  - **Merge** creates or extends a shared lax interface.
  - **Divorce** splits or dissolves one.
  - **Leave** keeps things as they are.

  Each decision is recorded with its reason. Record `leave` when a structural candidate has actually been considered and the decision is to preserve the current structure; do not record every pair that simply fails to merge. New qualifying evidence may justify considering the pair again. Metrics may inform review but never trigger a decision. [14.16.2, 14.16.2.1, 15.1, 14.11]
- **R16 — The merge test.** Merge only when all three hold: [14.16.1.20, 14.16.2.1]
  1. **Co-change:** the same change was needed in two or more places in this work item.
  2. **Same transformation:** in each place, the changed region is the same rule and could be written once.
  3. **Cause not excluded:** the diff matches none of the excluded causes (R17).

  One qualifying event is enough. Similar inputs, overlapping code or a shared output interface are never sufficient on their own.
- **R17 — Excluded causes.** Co-change from these causes is not merge evidence. Check them by comparing the diff against this list, not by inferring intent:
  1. **Rigid-interface ripple:** callers changed because a rigid interface changed, for example a library upgrade.
  2. **Shared-interface or shared-state ripple:** callers changed because a shared interface or shared state they all use changed. This includes caller updates made by this structure pass itself (R13, R14), and changes to a state schema.
  3. **Batch edit:** one request, refactor or codemod edited both places with no shared logic in the changed region. Exception: it qualifies when the changed region is literally the same transformation.
  4. **Asymmetric adaptation:** one requirement touched both places, but each needed its own adaptation. The symmetric case, where one rule is applied identically, may merge.
  5. **Drive-by edits:** convenience changes made "while here".

  If a co-change matches no exclusion but its cause cannot be determined, pause and record `unresolved`. Never merge automatically. [15.x confounds 1–4]
- **R18 — Shaping a merged interface.** The new interface reaches only as far as the regions that actually co-changed. Within that range, its contract must be stated without referring to its callers. "No interface; keep it inline" is a valid outcome. Coupling and cohesion metrics may validate a proposed boundary but never propose one. A boundary chosen only because it coincides with a change site is forbidden. [14.16.1.30, 14.16.1.31, 14.16.1.32, 14.16.1.27]
- **R19 — Divorce instead of flag parameters.** When serving divergent call sites would require a lax interface to take a flag or mode parameter, or when recorded `divergence` entries show its callers no longer want the same thing, split or dissolve the interface. Never add the flag.
- **R20 — Contract liveness check when callers are removed.** Whenever a change reduces an interface's call sites, check each contract clause for a remaining live reader using the registry. Remove the clauses no live caller uses. The check runs at the change that removed the callers, never as a sweep, and it runs whether or not a merge happened. [14.16.1.15]

### Verification

- **R21 — Verify behaviors, not fragments.** Verify each behavior through its input interface, observing the entry (input and state precondition), the results, and the interactions with external interfaces. Lax interfaces and helpers are not separate verification units by default, and helper tests never replace the behavior check. The number of test cases is not prescribed. [14.8, 14.16.1.12, 14.16.1.17]
- **R22 — Confirmed defects leave behavior-level regression coverage.** Add or update verification that would expose the defect through the affected behavior, where practicable. There is no one-test-per-bug rule. [11.4, 11.4.3]
- **R23 — Test cadence.** Run automated tests when a coherent behavior change is ready, not after every edit. Run the full suite and the registry/log checks at commit. Any failure blocks the commit and is resolved within the work item. [11.2, 2.11.1, 11.4.2]

### Accepted costs, human gates, activation

- **R24 — Name the accepted costs where they arise.** [14.8, 14.16.1.19, 14.16.1.29, 11.4.4]
  - Duplication by default means a bug echo can reach users twice.
  - Unmerged pairs are re-inspected at every relevant change until the merge test passes.
  - A misfit boundary adds inspection cost to every later change.
  - Tests document behavior and catch regressions; they are not assumed to prevent defects.
- **R25 — Pause for the operator when:**
  - a propagated change would alter externally visible behavior;
  - relevance, impact or co-change cause cannot be determined;
  - a rigid interface cannot meet the need through its existing contract;
  - the specification is ambiguous or a requirement decision is needed;
  - the registry check reports unresolved calls that affect the change.
- **R26 — Activation.** The skill activates on mentions of the emergent contract coding style, or when the repository's `AGENTS.md` (or equivalent) states that the project uses it, for example: "This project uses emergent contract coding; always use the `emergent-contract-coding` skill for development."

## 4. Script requirements

The scripts may be specific to the language and repository. The trial target's language comes first.

**Registry**
- **S1 — Generate.** Produce `registry.md` from source. For each interface, list its call sites (file + symbol), its direction (input, output or internal), and its change authority (rigid or lax). These are separate attributes and must not be treated as mutually exclusive categories. Output is deterministic with stable ordering, so registry diffs are meaningful in review.
- **S2 — Check.** Compare `registry.md` with the source. Exit non-zero on any difference and report added and removed call sites. Used in step 1 of the structure pass and at commit.
- **S3 — Classification source.** Read the classification from a declared, repository-level configuration:
  - which code is third-party or owned by others (rigid);
  - which functions are input interfaces (flows), for example by framework convention or annotation;
  - which interfaces are outputs, where this cannot be established from source or framework conventions;
  - which internal interfaces are lax.

  Direction (input, output or internal) and change authority (rigid or lax) are recorded independently. An input interface may be rigid when its contract is externally specified.

  Code outside the project's source tree defaults to rigid.
- **S4 — Unresolved calls are surfaced.** Calls that cannot be established statically appear in an explicit "Unresolved" section, never omitted: dynamic dispatch, reflection, generated code, framework callbacks. Resolutions are supplied through a resolutions input that the script reads, and each resolution is also recorded as a decision-log entry.
- **S5 — Affected-interface query.** Given a diff (or the working tree against HEAD), list the interfaces the change affected and all their call sites, as the input to structure-pass step 2. If call sites were removed, flag the interfaces for the liveness check (R20).

**Logs**
- **S6 — Append tool.** The agent writes to `decision-log.md` and `knowledge-log.md` only through an append command. The command validates the entry format, required fields, the entry kind and a non-empty reason, and rejects anything else.
- **S7 — Append-only check.** Verify that each log only grew relative to the last commit, with the earlier content byte-identical. Exit non-zero otherwise. Run at commit.

**General**
- **S8** — Every command gives human-readable output and has a meaningful exit code. Failures say what to fix.
- **S9** — The skill tells the agent to run these commands and never to edit `registry.md` directly.

## 5. Design decisions

- **Registry granularity** is one entry per call site, identified by the calling implementation. Registry content is structural and machine-verifiable. Explanations of intent belong in code, contracts or the knowledge log.
- **Load-bearing vs advisory logs:** the decision log is evidence the structure pass reads; the knowledge log is for people and is never consumed as evidence.
- **Cause attribution is best-effort.** The exclusion list is the operational substitute for classifying causes, and undetermined causes go to the operator.
- **Trial evidence:** implementation diffs, registry check results, behavior verification results, and log entries with reasons and work-item references. Metrics are review-time observations, never agent objectives.

## 6. Out of scope for this version

- Recursive restructuring: re-examining interfaces created or merged in the same pass, cascades where a middle interface's call count collapses, vertical merges, unrolling layers, and depth limits.
- Merging single-caller interfaces into their caller, including forwarders without behavior of their own.
- Promoting hidden inputs (configuration, reference data, rulesets) to interfaces, i.e. the blind-spot mitigation.
- Rules for throwaway test probes.
- Flow specifications as combined requirement/test/contract artifacts; a spec-derived registry; harvesting production examples; KPI instrumentation; numeric thresholds; naming modules after domain concepts.
- Existing codebases. The method assumes a project developed under it from the start.

## 7. How the methodology gets tested

The trial is real development under the skill on a chosen project, attended by the operator. Inspect diffs, registry check results, behavior verification and both logs. Evaluate:
- whether the structure pass finds the relevant call sites;
- whether registry drift stays visible;
- whether merges, divorces and leaves are defensible against R16–R19;
- whether the inspection and maintenance overhead is acceptable.

A short scripted series is unlikely to produce real merge evidence except through engineered or confounded pairs. Use a longer run of ordinary changes, and distinguish failures of the method from failures to communicate or execute it. If a merge turns out to be too eager under the one-event rule (R16), that is a trial finding, and divorce is the correction.

## 8. Open questions before the trial

1. **Verification entry points:** how the trial project exposes its behavior-level verification and full-suite command, including when repository agent/test instructions are absent.
2. **Classification configuration (S3):** the concrete format and how input interfaces are recognised in the trial project's framework.
