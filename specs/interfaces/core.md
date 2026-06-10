---
spec: core
kind: interface
defines:
  concepts:
    - Spec
    - Requirement
    - Decision
    - Invariant
    - DontCare
    - Verdict
    - Guard
    - Effect
    - Procedure
    - Footprint
    - Witness
    - Finding
    - Delta
  relations:
    - guard: Requirement -> Guard
    - effects: Requirement -> Effect+       # mechanical: vocabulary assignments
    - procedure: Requirement -> Procedure?  # judged: declared evaluation steps
    - overrides: Requirement -> Requirement*  # declared exceptions (D9)
    - footprint: Requirement -> Footprint   # = guard region (+ topics, if judged)
    - because: Requirement -> Decision*     # rationale links
    - supersedes: Decision -> Decision*
    - witness: Finding -> Witness?
  values:
    requirement.tier: [mechanical, judged]
    decision.status: [active, superseded]
    finding.kind: [conflict, gap, dead_rule, unknown_term,
                   duplicate_definition, stale_decision_ref, orphan_spec]
---

# Core interface

The shared vocabulary every behavior spec imports. Deliberately small: it
says what the objects *are* so that checking, querying, and authoring specs
can constrain what the system *does* with them, without re-punning the nouns.

A **Requirement** is the atomic unit of the system — not a type, not a data
model (see [[D1]] in `specs/checking.md`). Every requirement has a guard
(its domain: a region of situation space) and operative content checkable
at a declared tier (see [[D7]] in `specs/authoring.md`): **mechanical**
cards commit to structured `effects:` — assignments to vocabulary
variables, checked by enumeration; **judged** cards declare an explicit
evaluation procedure an agent executes, with verdicts marked as judgment
calls. A card with no check procedure cannot exist. A card's footprint is
its guard region; judged cards may add glossary topics.

**Invariant** cards claim a region of situation space is impossible;
**DontCare** cards accept any behavior in a possible region, with rationale
(see [[D10]] in `specs/checking.md`). **Verdict** cards record a designer
ruling about other cards (e.g. whether two judged cards conflict).

A **Decision** records a choice *and its rejected alternatives and reasons*.
Decisions are immutable once recorded: the only way to change one is a new
decision with a `supersedes:` link (see `specs/authoring.md`).
