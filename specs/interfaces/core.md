---
spec: core
kind: interface
defines:
  concepts:
    - Spec
    - Requirement
    - Criterion
    - Decision
    - Invariant
    - DontCare
    - Verdict
    - Guard
    - Effect
    - Frame
    - Procedure
    - Footprint
    - Witness
    - Finding
    - Delta
  relations:
    - guard: Requirement -> Guard
    - effects: Requirement -> Effect+       # assignments to vocabulary variables
    - frame: Requirement -> Frame?          # group frozen unless mentioned (D12)
    - overrides: Requirement -> Requirement*  # declared exceptions (D9)
    - footprint: Requirement -> Footprint   # = guard region
    - procedure: Criterion -> Procedure     # declared evaluation steps
    - footprint: Criterion -> Footprint     # declared topics/regions
    - rules_on: Verdict -> Criterion*       # designer ruling (CRI-R2)
    - because: Requirement -> Decision*     # rationale links
    - supersedes: Decision -> Decision*
    - witness: Finding -> Witness?
  values:
    card.kind: [requirement, criterion, decision, invariant, dont_care, verdict]
    decision.status: [active, superseded]
    finding.kind: [conflict, gap, dead_rule, unknown_term,
                   duplicate_definition, stale_decision_ref, orphan_spec]
---

# Core interface

The shared vocabulary every behavior spec imports. Deliberately small: it
says what the objects *are* so that checking, querying, and authoring specs
can constrain what the system *does* with them, without re-punning the nouns.

A **Requirement** is the atomic unit of the spec proper — not a type, not
a data model (see [[D1]] in `specs/checking.md`). It is fully mechanical:
a guard (its domain: a region of situation space) plus structured
`effects:` — assignments to vocabulary variables, checked by enumeration.
An optional `frame:` names a variable group frozen unless mentioned; it
desugars to `-> unchanged` effects (see [[D12]] in `specs/checking.md`).
Its footprint is exactly its guard region.

A **Criterion** is the judged layer (see [[D11]] in `specs/criteria.md`):
a footprint plus a declared evaluation Procedure an agent executes at
review time, with verdicts marked as judgment calls. Criteria never count
toward coverage and have no check-time conflict semantics. A card with no
check procedure — mechanical or judged — cannot exist.

**Invariant** cards claim a region of situation space is impossible;
**DontCare** cards accept any behavior in a possible region, with rationale
(see [[D10]] in `specs/checking.md`). **Verdict** cards record a designer
ruling on contradictory criteria (see CRI-R2 in `specs/criteria.md`).

A **Decision** records a choice *and its rejected alternatives and reasons*.
Decisions are immutable once recorded: the only way to change one is a new
decision with a `supersedes:` link (see `specs/authoring.md`).
